# Comprehensive RAG Testing Guide for Veterans Survey Data

## 1. Data Upload Instructions

1. **Save the TXT file:**
   - Use the data from paste.txt containing 30 survey records
   - Keep the CSV format within the text file (headers + comma-separated values)
   - Make sure all quotes and special characters are preserved correctly

2. **Upload to your RAG system:**
   - Log in to your deployed PubSec-Info-Assistant instance
   - Upload the text file using the document upload functionality
   - Allow time for processing and indexing (usually 5-10 minutes)

3. **Verify successful upload:**
   - Check that the file appears in your document list
   - Confirm it's properly indexed by asking a simple test question: "How many comments mention wait time?"

## 2. Testing Categories and Questions

### CATEGORY A: Questions RAG Should Answer Successfully

These questions leverage RAG's strengths in retrieving and understanding text content.

#### A1. Specific Comment Retrieval

**Question:** "What was the comment about telehealth at Ann Arbor VA Medical Center?"

**Expected Answer:** "The telehealth option saved me a long drive. The doctor was punctual for our video appointment and the technology worked flawlessly. Great alternative for routine follow-ups."

**Why RAG Should Succeed:** This is a straightforward retrieval task requiring only keyword matching and relevance ranking. The system needs to find comments containing "telehealth" and "Ann Arbor," which is explicit metadata in the dataset. The relevant record (comment_id: 13) should be easily retrieved based on these parameters.

**Your Observation:** 
[Record the actual RAG response here]

#### A2. Topic Identification

**Question:** "What topics are mentioned in relation to the PTSD program at Detroit VA Medical Center?"

**Expected Answer:** The PTSD program at Detroit is mentioned with topics including mental health, PTSD program, staff expertise, well-organized group sessions, therapists experienced with veteran-specific issues, and being described as life-changing.

**Why RAG Should Succeed:** This question requires identifying specific comments about a particular program at a specific facility, then extracting the associated topics. The information is explicitly stated in comments 22 and 25, and the topic fields clearly list these concepts. This plays to RAG's strength in semantic search and information extraction.

**Your Observation:** 
[Record the actual RAG response here]

#### A3. Sentiment Analysis

**Question:** "What are the main complaints about the food at VA facilities based on the negative comments?"

**Expected Answer:** Complaints about food include: terrible food, limited menu options not suitable for diabetics, and the kitchen seeming to have limited options. This was mentioned in an inpatient stay at Detroit VA Medical Center.

**Why RAG Should Succeed:** This requires finding comments with negative sentiment that mention food, which should be straightforward for the RAG system using a combination of metadata filtering (sentiment=Negative) and keyword search ("food"). The system can then extract and summarize the specific complaints, which is a core capability of generative AI.

**Your Observation:** 
[Record the actual RAG response here]

#### A4. Facility Comparison (Text-Based)

**Question:** "How do comments about mental health services differ between the three VA Medical Centers?"

**Expected Answer:** All three facilities receive positive comments about mental health services. Battle Creek's mental health clinic staff is described as wonderful, attentive, and caring with great group therapy rooms. Ann Arbor mentions improved services with attentive therapists and better privacy in therapy rooms. Detroit's PTSD program is particularly highlighted as excellent, with well-organized group sessions and therapists experienced with veteran-specific issues, described as "life-changing."

**Why RAG Should Succeed:** This requires semantic understanding to identify mental health-related comments across all facilities and compare them. While it involves multiple dimensions, it's still primarily a text understanding task without complex calculations. The RAG system should be able to retrieve relevant comments and generate a comparative summary.

**Your Observation:** 
[Record the actual RAG response here]

#### A5. Pattern Recognition in Comments

**Question:** "What suggestions for improvement are mentioned by veterans in their comments?"

**Expected Answer:** Suggestions include: improving weekend staffing levels, better coordination regarding medication instructions, reducing wait times for appointments with specialists, making transition services less confusing, providing clearer answers about benefits, improving the appointment scheduling system, and offering more suitable dietary options for patients with specific needs like diabetes.

**Why RAG Should Succeed:** This leverages the language model's ability to identify implied suggestions within comments. While not explicitly labeled as "suggestions," the model can recognize phrases indicating desired improvements. This demonstrates RAG's strength in semantic understanding beyond simple keyword matching.

**Your Observation:** 
[Record the actual RAG response here]

### CATEGORY B: Questions Where RAG Will Likely Struggle

These questions test the limitations of RAG systems with numerical calculations and data aggregation.

#### B1. Retrieval Limitation Test

**Question:** "How many total survey responses are there for all facilities in the dataset?"

**Expected Answer:** 30 total survey responses (10 for Battle Creek, 10 for Ann Arbor, and 10 for Detroit)

**Why RAG Will Struggle:** This question reveals a fundamental limitation of RAG systems. When processing large datasets, RAG typically retrieves only a subset of relevant documents (often limited to top-k results based on similarity scoring). With default settings, it might only retrieve 3-5 documents, which means it will vastly undercount the total. This limitation directly impacts all aggregation questions because the system simply doesn't "see" all the relevant data.

**Your Observation:** 
[Record the actual RAG response here]

#### B2. Daily Min/Max/Average Scores

**Question:** "What were the minimum, maximum, and average satisfaction scores for Battle Creek VA Medical Center on January 4, 2025?"

**Expected Answer:** 
- Minimum: 2 (from comment_id: 6)
- Maximum: 5 (from comment_id: 5)
- Average: 3.5 (Sum of scores: 5+2 = 7, divided by 2 = 3.5)

**Why RAG Will Struggle:** This question requires multiple steps that challenge RAG systems:
1. Filtering by specific date (requiring datetime understanding)
2. Filtering by facility
3. Identifying min and max values across multiple records
4. Calculating an average 
The system must retrieve ALL relevant records for the date, which is unlikely given retrieval limitations. Even small retrieval errors will lead to incorrect calculations.

**Your Observation:** 
[Record the actual RAG response here]

#### B3. Facility Comparison by Survey Type

**Question:** "Compare the average satisfaction scores for Outpatient services between all three facilities."

**Expected Answer:**
- Battle Creek: 3.17 (Sum of scores: 5+1+2+4+5+2 = 19, divided by 6 = 3.17)
- Ann Arbor: 3.83 (Sum of scores: 3+4+4+4+3+4 = 22, divided by 6 = 3.67)
- Detroit: 4.0 (Sum of scores: 4+5+4+4+5+2 = 24, divided by 6 = 4.0)
- Conclusion: Detroit VA Medical Center has the highest average satisfaction score for Outpatient services, followed by Ann Arbor, then Battle Creek.

**Why RAG Will Struggle:** This requires filtering by survey type and facility, then performing calculations for each group. The system needs to:
1. Correctly identify all Outpatient records for each facility
2. Calculate three separate averages
3. Compare the results
Multiple calculation steps combined with retrieval limitations make this type of comparison particularly challenging for RAG systems.

**Your Observation:** 
[Record the actual RAG response here]

#### B4. Survey Type Analysis Across Facilities

**Question:** "What's the average trust score for each survey type across all facilities?"

**Expected Answer:**
- Outpatient: 3.78 (Average of 18 Outpatient trust scores)
- Inpatient: 3.33 (Average of 6 Inpatient trust scores)
- AMA: 2.67 (Average of 3 AMA trust scores)
- BTSS: 2.67 (Average of 3 BTSS trust scores)

**Why RAG Will Struggle:** This requires grouping by survey type across all facilities and calculating averages for each group. The complexity comes from:
1. Needing to retrieve ALL records for each survey type
2. Grouping them correctly
3. Performing multiple calculations
4. Comparing results across different categories
This multi-dimensional analysis is particularly difficult for RAG systems.

**Your Observation:** 
[Record the actual RAG response here]

#### B5. Sentiment Correlation Analysis

**Question:** "Is there a correlation between sentiment and satisfaction scores in the survey data?"

**Expected Answer:** There is a strong correlation between sentiment and satisfaction scores. Positive sentiment comments have an average satisfaction score of 4.27, Neutral comments average 3.0, and Negative comments average 1.92. This shows that satisfaction scores consistently align with the sentiment expressed in comments.

**Why RAG Will Struggle:** This requires:
1. Grouping all records by sentiment
2. Calculating average satisfaction for each sentiment group
3. Identifying the pattern/correlation between the variables
This type of statistical analysis is beyond what RAG systems typically handle well, especially since it requires analyzing the entire dataset simultaneously.

**Your Observation:** 
[Record the actual RAG response here]

#### B6. Weekday vs. Weekend Analysis

**Question:** "Is there a difference in satisfaction scores between weekday and weekend comments at Battle Creek VA Medical Center?"

**Expected Answer:** There is only one explicitly mentioned weekend comment (comment_id: 7) at Battle Creek with a satisfaction score of 1, compared to the other comments which are presumably weekday and have an average satisfaction score of approximately 3.11. This suggests lower satisfaction on weekends, but the sample size is too small for definitive conclusions.

**Why RAG Will Struggle:** This requires:
1. Understanding the concept of weekdays vs. weekends
2. Finding comments that explicitly or implicitly mention weekend care
3. Comparing scores between two different groups
4. Drawing a conclusion from limited data
The conceptual understanding combined with grouping and calculation makes this particularly challenging for RAG systems.

**Your Observation:** 
[Record the actual RAG response here]

## 3. Testing the Pre-Computation Solution

After testing the questions above and documenting the limitations, you can demonstrate how pre-computation improves results:

1. **Create a pre-computed statistics document:**
   - Create a text file with calculated statistics like:
   ```
   Battle Creek VA Medical Center Statistics:
   - Total survey responses: 10
   - Outpatient responses: 6
   - Average satisfaction score: 3.0
   - Average satisfaction by survey type: Outpatient (3.17), Inpatient (2.5), AMA (3.0), BTSS (2.0)
   - January 4 statistics: Min satisfaction (2), Max satisfaction (5), Average satisfaction (3.5)
   ...
   ```

2. **Upload this document alongside your raw data**

3. **Test the same questions again:**
   - Ask questions B2-B6 again
   - Document if the system can now retrieve and report the pre-computed statistics

## 4. Summary and Observations

After completing your testing, use this section to document key findings:

1. **Retrieval Limitations:**
   - Did the system consistently retrieve all relevant records for questions?
   - At what point did comprehensive retrieval break down?

2. **Calculation Accuracy:**
   - How accurate were simple calculations?
   - How accurate were complex multi-step calculations?

3. **Pre-computation Effectiveness:**
   - Did pre-computed statistics improve accuracy?
   - What types of questions still posed challenges even with pre-computation?

4. **Recommendations for Implementation:**
   - Which types of questions should rely on RAG?
   - Which types should use traditional analytics?
   - What pre-computed statistics would be most valuable?
