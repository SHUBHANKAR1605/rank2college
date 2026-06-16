USE rank2college;

SELECT 
    institute_type AS "College Type", 
    COUNT(*) AS "Total Rows" 
FROM 
    college_cutoffs 
GROUP BY 
    institute_type;