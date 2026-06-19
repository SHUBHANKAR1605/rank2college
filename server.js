require('dotenv').config(); // <-- This MUST be at the very top!
const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Tell MySQL to look in your hidden .env file instead of hardcoding it here
const db = mysql.createConnection({
    host: process.env.DB_HOST,
    port: process.env.DB_PORT, // <-- This is the critical line you needed!
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD, 
    database: process.env.DB_NAME
});

app.post('/api/predict', (req, res) => {
    const { examType, crlRank, category, catRank, gender, quota, branchKeyword } = req.body;
    const rank = parseInt(crlRank);
    const cRank = parseInt(catRank);
    const MARGIN = 0.10;

    const chance_sql = `
        CASE
            WHEN c.seat_type = 'OPEN' AND c.closing_rank >= ? THEN 'SAFE'
            WHEN c.seat_type = 'OPEN' AND c.closing_rank >= ? * 0.97 THEN 'LIKELY'
            WHEN c.seat_type = 'OPEN' AND c.closing_rank >= ? * 0.93 THEN 'MODERATE'
            WHEN c.seat_type = 'OPEN' THEN 'STRETCH'
            WHEN c.seat_type != 'OPEN' AND c.closing_rank >= ? THEN 'SAFE'
            WHEN c.seat_type != 'OPEN' AND c.closing_rank >= ? * 0.97 THEN 'LIKELY'
            WHEN c.seat_type != 'OPEN' AND c.closing_rank >= ? * 0.93 THEN 'MODERATE'
            ELSE 'STRETCH'
        END
    `;
    let params = [rank, rank, rank, cRank, cRank, cRank];

    let exam_filter = (examType === "2") ? "c.institute_type = 'IIT' AND c.quota = 'AI'" : 
                      (quota === "HS") ? "((c.institute_type = 'NIT' AND c.quota = 'HS') OR (c.institute_type = 'IIIT' AND c.quota = 'AI') OR (c.institute_type = 'GFTI' AND c.quota IN ('AI','HS')))" :
                      "((c.institute_type = 'NIT' AND c.quota = 'OS') OR (c.institute_type = 'IIIT' AND c.quota = 'AI') OR (c.institute_type = 'GFTI' AND c.quota IN ('AI','OS')))";

    let gender_filter = (gender === "female") ? "AND c.gender LIKE 'Female%'" : (gender === "neutral") ? "AND c.gender = 'Gender-Neutral'" : "";
    
    let cat_filter = (category === "OPEN") ? "AND c.seat_type = 'OPEN' AND c.closing_rank BETWEEN ? AND ?" : "AND c.seat_type = ? AND c.closing_rank BETWEEN ? AND ?";
    if (category === "OPEN") params.push(Math.floor(rank * (1 - MARGIN)), Math.floor(rank * (1 + MARGIN)));
    else params.push(category, Math.floor(cRank * (1 - MARGIN)), Math.floor(cRank * (1 + MARGIN)));

    let branch_filter = branchKeyword ? "AND c.branch_name LIKE ?" : "";
    if (branchKeyword) params.push(`%${branchKeyword}%`);

    const query = `
        SELECT c.institute_name as institute, c.branch_name as branch, c.quota, c.seat_type as seat, c.closing_rank as \`rank\`, (${chance_sql}) as chance
        FROM college_cutoffs c
        WHERE ${exam_filter} ${gender_filter} ${cat_filter} ${branch_filter}
        ORDER BY FIELD(chance, 'SAFE','LIKELY','MODERATE','STRETCH'), c.closing_rank ASC
    `;

    db.query(query, params, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));