# Comprehensive RAG Testing Guide for Veterans Survey Data

## 1. Data Upload Instructions

1. **Save the CSV file:**
   - Copy the complete CSV data from the "Revised Veterans Survey Sample Data" artifact
   - Save it as `veterans_survey_data.csv` on your computer
   - Ensure all 88 records are included with complete fields

2. **Upload to your RAG system:**
   - Log in to your deployed PubSec-Info-Assistant instance
   - Upload the CSV file using the document upload functionality
   - Allow time for processing and indexing (usually 5-10 minutes)

3. **Verify successful upload:**
   - Check that the file appears in your document list
   - Confirm it's properly indexed by asking a simple test question: "How many comments mention wait time?"

## 2. Testing Categories and Questions

### CATEGORY A: Questions RAG Should Answer Successfully

These questions leverage RAG's strengths in retrieving and understanding text content.

#### A1. Specific Comment Retrieval

**Question:** "What was the comment about telehealth at Battle Creek VA Medical Center in February?"

**Expected Answer:** "The telehealth option saved me a long drive. The doctor was punctual for our video appointment and the technology worked flawlessly. Great alternative for routine follow-ups."

**Why RAG Should Succeed:** This is a straightforward retrieval task requiring only keyword matching and relevance ranking. The system needs to find comments containing "telehealth" and "Battle Creek" from February, which is explicit metadata in the dataset. The relevant record (comment_id: 22) should be easily retrieved based on these parameters.

**Your Observation:** 
[Record the actual RAG response here]

#### A2. Topic Identification

**Question:** "What topics are mentioned in relation to the PTSD program at Ann Arbor VA Medical Center?"

**Expected Answer:** The PTSD program at Ann Arbor is mentioned with topics including mental health, PTSD program, staff expertise, life-changing treatment, well-organized group sessions, and therapists experienced with veteran-specific issues.

**Why RAG Should Succeed:** This question requires identifying specific comments about a particular program at a specific facility, then extracting the associated topics. The information is explicitly stated in comments 31, 46, and 51, and the topic fields clearly list these concepts. This plays to RAG's strength in semantic search and information extraction.

**Your Observation:** 
[Record the actual RAG response here]

#### A3. Sentiment Analysis

**Question:** "What are the main complaints about the food at VA facilities based on the negative comments?"

**Expected Answer:** Complaints about food include: bland food, food being cold when delivered, terrible menu options, limited options not suitable for diabetics, and kitchen seeming to have limited food options. These issues were mentioned in inpatient stays across different facilities.

**Why RAG Should Succeed:** This requires finding comments with negative sentiment that mention food, which should be straightforward for the RAG system using a combination of metadata filtering (sentiment=Negative) and keyword search ("food"). The system can then extract and summarize the specific complaints, which is a core capability of generative AI.

**Your Observation:** 
[Record the actual RAG response here]

#### A4. Facility Comparison (Text-Based)

**Question:** "How do comments about technology differ between Battle Creek and Ann Arbor VA Medical Centers?"

**Expected Answer:** Both facilities receive positive comments about technology. Battle Creek comments mention telehealth options, electronic check-in, online prescription refills, and patient portals. Ann Arbor comments highlight check-in kiosks, telehealth systems, and the online tracking portal for benefits. Both facilities' veterans appreciate technology that saves time and increases convenience.

**Why RAG Should Succeed:** This requires semantic understanding to identify technology-related comments across two facilities and compare them. While it involves multiple dimensions, it's still primarily a text understanding task without complex calculations. The RAG system should be able to retrieve relevant comments and generate a comparative summary.

**Your Observation:** 
[Record the actual RAG response here]

#### A5. Pattern Recognition in Comments

**Question:** "What suggestions for improvement are mentioned by veterans in their comments?"

**Expected Answer:** Suggestions include: adding more disabled parking spaces, improving appointment scheduling systems, reducing wait times, increasing weekend staffing, better training for staff on policies, digitizing paperwork, creating more partnerships with local businesses for veteran employment, improving the discharge process, and enhancing the prescription refill process.

**Why RAG Should Succeed:** This leverages the language model's ability to identify implied suggestions within comments. While not explicitly labeled as "suggestions," the model can recognize phrases indicating desired improvements. This demonstrates RAG's strength in semantic understanding beyond simple keyword matching.

**Your Observation:** 
[Record the actual RAG response here]

### CATEGORY B: Questions Where RAG Will Likely Struggle

These questions test the limitations of RAG systems with numerical calculations and data aggregation.

#### B1. Retrieval Limitation Test

**Question:** "How many total survey responses are there for all facilities in the dataset?"

**Expected Answer:** 88 total survey responses (29 for Battle Creek, 30 for Ann Arbor, and 29 for Detroit)

**Why RAG Will Struggle:** This question reveals a fundamental limitation of RAG systems. When processing large datasets, RAG typically retrieves only a subset of relevant documents (often limited to top-k results based on similarity scoring). With default settings, it might only retrieve 3-5 documents, which means it will vastly undercount the total. This limitation directly impacts all aggregation questions because the system simply doesn't "see" all the relevant data.

**Your Observation:** 
[Record the actual RAG response here]

#### B2. Basic Facility Average

**Question:** "What is the average satisfaction score for Battle Creek VA Medical Center?"

**Expected Answer:** 3.24 (Sum of all satisfaction scores for Battle Creek divided by 29 records)

**Why RAG Will Struggle:** While this calculation seems simple, RAG systems often make errors in mathematical operations. The system needs to accurately identify all relevant records, extract the numerical values, and perform the calculation without error. Even small mistakes in counting or addition can lead to incorrect results. More importantly, as demonstrated in question B1, the system often doesn't retrieve all relevant records, leading to calculations based on incomplete
