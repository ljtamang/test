# RAG Capability Analysis for VA Survey Data

This document provides a structured analysis of what Retrieval-Augmented Generation (RAG) can and cannot effectively do with VA medical center survey data. Each question includes:
1. The specific question to test
2. The expected answer based on the data
3. Explanation of why RAG will succeed or struggle
4. SQL query to verify results in Databricks
5. Space to record actual RAG responses

## CATEGORY A: Questions RAG Should Answer Successfully
These questions leverage RAG's strengths in retrieving and understanding text content.

### A1. Specific Comment Retrieval
**Question:** "What was the comment about telehealth at Ann Arbor VA Medical Center?"

**Expected Answer:** "The telehealth option saved me a long drive. The doctor was punctual for our video appointment and the technology worked flawlessly. Great alternative for routine follow-ups."

**Why RAG Should Succeed:** This is a straightforward retrieval task requiring only keyword matching and relevance ranking. The system needs to find comments containing "telehealth" and "Ann Arbor," which is explicit in the dataset. The relevant record (comment_id: 13) should be easily retrieved based on these parameters.

**SQL Query:**
```sql
SELECT comment_id, comment
FROM test_db.test_vsignla_data
WHERE facility_name = 'Ann Arbor VA Medical Center'
  AND comment LIKE '%telehealth%';
```

**Your Observation:** [Record the actual RAG response here]

### A2. Topic Identification
**Question:** "What topics are mentioned in relation to the PTSD program at Detroit VA Medical Center?"

**Expected Answer:** The PTSD program at Detroit is mentioned with topics including mental health, PTSD program, staff expertise, group sessions, and therapist expertise. Comments describe it as "life-changing" with staff who are "experts in mental health and veteran-specific issues."

**Why RAG Should Succeed:** This question requires identifying specific comments about a particular program at a specific facility, then extracting the associated topics. The information is explicitly stated in comments 22 and 25, and the topic fields clearly list these concepts.

**SQL Query:**
```sql
SELECT comment_id, comment, topics
FROM test_db.test_vsignla_data
WHERE facility_name = 'Detroit VA Medical Center'
  AND (comment LIKE '%PTSD%' OR topics LIKE '%PTSD%');
```

**Your Observation:** [Record the actual RAG response here]

### A3. Sentiment Analysis
**Question:** "What are the main complaints about the food at VA facilities based on the negative comments?"

**Expected Answer:** Based on comment_id 35, complaints about food include: "terrible food, very limited menu options not suitable for diabetics" at Detroit VA Medical Center with a negative sentiment.

**Why RAG Should Succeed:** This requires finding comments with negative sentiment that mention food, which should be straightforward using a combination of metadata filtering (sentiment=Negative) and keyword search ("food").

**SQL Query:**
```sql
SELECT comment_id, facility_name, comment
FROM test_db.test_vsignla_data
WHERE sentiment = 'Negative'
  AND comment LIKE '%food%';
```

**Your Observation:** [Record the actual RAG response here]

### A4. Facility Comparison (Text-Based)
**Question:** "How do comments about mental health services differ between the three VA Medical Centers?"

**Expected Answer:** Battle Creek's mental health clinic staff is described as "wonderful, attentive, and caring" with "great group therapy rooms" (comment_id 45). Detroit's PTSD program is highlighted as "life-changing" with "experts in mental health and veteran-specific issues" (comment_id 22) and having "well-organized group sessions and experienced therapists" (comment_id 25). Ann Arbor doesn't have specific mental health comments in this dataset.

**Why RAG Should Succeed:** This requires semantic understanding to identify mental health-related comments across facilities and compare them. While it involves multiple dimensions, it's still primarily a text understanding task.

**SQL Query:**
```sql
SELECT facility_name, comment_id, comment, topics
FROM test_db.test_vsignla_data
WHERE topics LIKE '%mental health%' 
   OR comment LIKE '%mental health%'
   OR topics LIKE '%PTSD%'
   OR comment LIKE '%PTSD%'
   OR topics LIKE '%therapy%'
   OR comment LIKE '%therapy%'
ORDER BY facility_name;
```

**Your Observation:** [Record the actual RAG response here]

### A5. Pattern Recognition in Comments
**Question:** "What suggestions for improvement are mentioned in the comments with negative sentiment?"

**Expected Answer:** Improvement suggestions from negative comments include: reducing wait times and improving communication regarding appointments, addressing staff shortages that impact patient care, improving administrative processes to prevent paperwork errors, and providing better food options for patients with specific needs like diabetes.

**Why RAG Should Succeed:** This leverages the language model's ability to identify implied suggestions within negative comments. While not explicitly labeled as "suggestions," the model can recognize phrases indicating desired improvements.

**SQL Query:**
```sql
SELECT comment_id, facility_name, comment, topics
FROM test_db.test_vsignla_data
WHERE sentiment = 'Negative'
ORDER BY comment_id;
```

**Your Observation:** [Record the actual RAG response here]

## CATEGORY B: Questions Where RAG Will Likely Struggle
These questions test the limitations of RAG systems with numerical calculations and data aggregation.

### B1. Retrieval Limitation Test
**Question:** "How many total survey responses are there for each facility in the dataset?"

**Expected Answer:** 
- Ann Arbor VA Medical Center: 94 survey responses
- Battle Creek VA Medical Center: 103 survey responses
- Detroit VA Medical Center: 3 survey responses
- Total: 200 survey responses

**Why RAG Will Struggle:** This requires counting all records in the dataset. RAG typically retrieves only a subset of documents based on relevance scoring, so it will likely undercount the total. This limitation impacts all aggregation questions because the system simply doesn't "see" all the relevant data.

**SQL Query:**
```sql
SELECT facility_name, COUNT(*) as response_count
FROM test_db.test_vsignla_data
GROUP BY facility_name
ORDER BY facility_name;
```

**Your Observation:** [Record the actual RAG response here]

### B2. Daily Min/Max/Average Scores
**Question:** "What were the minimum, maximum, and average satisfaction scores for Battle Creek VA Medical Center on January 4, 2025?"

**Expected Answer:**
- Minimum satisfaction score: 3 (from comment_id 42)
- Maximum satisfaction score: 5 (from comment_id 46)
- Average satisfaction score: 4.0 (Sum of scores: 3+4+4+5 = 16, divided by 4 = 4.0)

**Why RAG Will Struggle:** RAG systems struggle with computational questions due to retrieval limitations:

1. **Incomplete data retrieval**: They retrieve only a subset of documents rather than all matching records
   
2. **Misleading accuracy**: Min/max values might appear correct by coincidence. If satisfaction scores of 3 and 5 appear frequently throughout the dataset, RAG might retrieve documents containing these values even if they're not the right date-specific records. This creates an illusion of accuracy.
   
3. **Average calculations will be wrong**: Even if min/max accidentally appear correct, the average calculation will almost certainly be wrong because it requires all relevant records.
   
4. **No validation mechanism**: RAG has no way to verify it has retrieved all relevant records before performing calculations.

This highlights why RAG is fundamentally unsuited for precise mathematical operations on structured data - the results may sometimes appear plausible but cannot be relied upon.

**SQL Query:**
```sql
SELECT 
  MIN(satisfaction) as min_satisfaction,
  MAX(satisfaction) as max_satisfaction,
  AVG(satisfaction) as avg_satisfaction,
  COUNT(*) as comment_count
FROM test_db.test_vsignla_data
WHERE facility_name = 'Battle Creek VA Medical Center'
  AND CAST(responsedate AS DATE) = '2025-01-04';
```

**Your Observation:** [Record the actual RAG response here]

### B3. Facility Comparison by Survey Type
**Question:** "Compare the average satisfaction scores for Outpatient services between Ann Arbor and Battle Creek VA Medical Centers in January 2025."

**Expected Answer:**
- Ann Arbor (Outpatient): 3.2 average satisfaction (Sum: 32, Count: 10)
- Battle Creek (Outpatient): 3.0 average satisfaction (Sum: 30, Count: 10)
- Conclusion: Ann Arbor VA Medical Center has a slightly higher average satisfaction score for Outpatient services in January 2025.

**Why RAG Will Struggle:** This requires filtering by survey type, facility, and date range, then performing calculations for each group. Multiple calculation steps combined with retrieval limitations make this comparison challenging.

**SQL Query:**
```sql
SELECT 
  facility_name,
  AVG(satisfaction) as avg_satisfaction,
  COUNT(*) as comment_count,
  SUM(satisfaction) as sum_satisfaction
FROM test_db.test_vsignla_data
WHERE surveytype = 'Outpatient'
  AND facility_name IN ('Ann Arbor VA Medical Center', 'Battle Creek VA Medical Center')
  AND responsedate >= '2025-01-01' 
  AND responsedate < '2025-02-01'
GROUP BY facility_name
ORDER BY facility_name;
```

**Your Observation:** [Record the actual RAG response here]

### B4. Survey Type Analysis Across Facilities
**Question:** "What's the average trust score for each survey type across all facilities?"

**Expected Answer:**
- Outpatient: 3.15 average trust score (Sum: 315, Count: 100)
- Inpatient: 3.13 average trust score (Sum: 313, Count: 100)

**Why RAG Will Struggle:** This requires grouping by survey type across all facilities and calculating averages for each group. The complexity comes from needing to retrieve ALL records for each survey type, grouping them correctly, and performing calculations.

**SQL Query:**
```sql
SELECT 
  surveytype,
  AVG(trust) as avg_trust_score,
  COUNT(*) as response_count,
  SUM(trust) as sum_trust
FROM test_db.test_vsignla_data
GROUP BY surveytype
ORDER BY surveytype;
```

**Your Observation:** [Record the actual RAG response here]

### B5. Sentiment Correlation Analysis
**Question:** "Is there a correlation between sentiment and satisfaction scores in the survey data?"

**Expected Answer:** There appears to be a correlation between sentiment and satisfaction scores:
- Positive sentiment comments have an average satisfaction score of approximately 3.59
- Neutral sentiment comments have an average satisfaction score of approximately 3.24
- Negative sentiment comments have an average satisfaction score of approximately 2.78
This indicates that satisfaction scores tend to be higher for positive sentiment comments and lower for negative sentiment comments.

**Why RAG Will Struggle:** This requires grouping all records by sentiment, calculating average satisfaction for each sentiment group, and identifying patterns between variables. This type of statistical analysis requires analyzing the entire dataset simultaneously.

**SQL Query:**
```sql
SELECT 
  sentiment,
  AVG(satisfaction) as avg_satisfaction,
  COUNT(*) as response_count,
  STDDEV(satisfaction) as std_deviation,
  MIN(satisfaction) as min_satisfaction,
  MAX(satisfaction) as max_satisfaction
FROM test_db.test_vsignla_data
GROUP BY sentiment
ORDER BY avg_satisfaction DESC;
```

**Your Observation:** [Record the actual RAG response here]

### B6. Time-Based Trend Analysis
**Question:** "Is there a difference in satisfaction scores between weekdays and weekend comments at Battle Creek VA Medical Center?"

**Expected Answer:** There is only one explicitly mentioned weekend comment (comment_id: 7) at Battle Creek with a satisfaction score of 1, compared to the weekday comments which have an average satisfaction score of approximately 3.05. This suggests lower satisfaction on weekends, but the sample size is too small for definitive conclusions.

**Why RAG Will Struggle:** This question requires several capabilities that challenge RAG systems:

1. **Conceptual understanding**: RAG needs to understand the concept of weekdays vs. weekends and translate dates into day types
   
2. **Implicit information extraction**: The system must identify which records are from weekends (either explicitly mentioned or by analyzing the dates)
   
3. **Comprehensive data analysis**: All records need to be properly categorized and included in calculations
   
4. **Multi-stage reasoning**: The system must perform grouping, calculation, and comparison operations

Even if RAG could reliably extract dates from all relevant records (which is challenging given retrieval limitations), it would still need to correctly categorize each date as weekday or weekend before performing calculations and comparisons. This combination of conceptual understanding and multi-stage numerical analysis is particularly difficult for RAG systems.

**SQL Query:**
```sql
SELECT 
  CASE 
    WHEN DAYOFWEEK(responsedate) IN (1, 7) THEN 'Weekend'
    ELSE 'Weekday' 
  END as day_type,
  AVG(satisfaction) as avg_satisfaction,
  COUNT(*) as comment_count,
  MIN(satisfaction) as min_satisfaction,
  MAX(satisfaction) as max_satisfaction
FROM test_db.test_vsignla_data
WHERE facility_name = 'Battle Creek VA Medical Center'
GROUP BY CASE 
    WHEN DAYOFWEEK(responsedate) IN (1, 7) THEN 'Weekend'
    ELSE 'Weekday' 
  END
ORDER BY day_type;
```

**Your Observation:** [Record the actual RAG response here]

## Additional Useful Queries for Your Analysis

### Comment Distribution by Sentiment and Facility

```sql
SELECT 
  facility_name,
  sentiment,
  COUNT(*) as comment_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY facility_name), 2) as percentage
FROM test_db.test_vsignla_data
GROUP BY facility_name, sentiment
ORDER BY facility_name, sentiment;
```

### Top Topics by Facility

```sql
WITH topic_split AS (
  SELECT 
    facility_name,
    TRIM(value) as topic
  FROM test_db.test_vsignla_data
  LATERAL VIEW EXPLODE(SPLIT(topics, ';')) t AS value
  WHERE topics IS NOT NULL
)

SELECT 
  facility_name,
  topic,
  COUNT(*) as topic_count
FROM topic_split
GROUP BY facility_name, topic
ORDER BY facility_name, topic_count DESC;
```

### Satisfaction Score Trends by Week

```sql
SELECT 
  facility_name,
  DATE_TRUNC('week', responsedate) as week,
  AVG(satisfaction) as avg_satisfaction,
  COUNT(*) as response_count
FROM test_db.test_vsignla_data
GROUP BY facility_name, DATE_TRUNC('week', responsedate)
ORDER BY facility_name, week;
```

## Conclusion on RAG Capabilities

Based on the structure of these questions, we expect RAG to perform well on:
1. Finding specific information based on keywords
2. Identifying topics associated with specific facilities or programs
3. Extracting sentiment-based insights
4. Making text-based comparisons
5. Recognizing patterns in comments

RAG will likely struggle with:
1. Counting total records across the entire dataset
2. Performing calculations that require complete data retrieval
3. Comparing numerical values across different groupings
4. Analyzing correlations between variables
5. Identifying time-based trends

**Deceptive Accuracy Issues:**
A particularly concerning issue is that RAG might give seemingly correct answers to quantitative questions by coincidence. For example:
- Min/max values might appear correct if common values (like 1 and 5 on a 5-point scale) happen to be included in the retrieved documents
- Simple counts might seem plausible even when drastically undercounted
- These deceptive "hits" create false confidence in the system's mathematical capabilities

The key limitation isn't that RAG can't perform mathematical operations - it can. The issue is that RAG systems:
- Retrieve only a subset of documents rather than the complete matching set
- Have no mechanism to verify data completeness before calculation
- Cannot guarantee consistent results for identical quantitative queries

This capability assessment will help your technical leadership understand where RAG excels (information retrieval and understanding) and where it has limitations (comprehensive data operations) when working with structured VA survey data.

For best results, consider a hybrid approach where:
- RAG handles qualitative analysis, sentiment understanding, and specific information retrieval
- SQL queries handle quantitative analysis, trends, and aggregations

This combination will provide the most comprehensive insights from your VA survey data.
