

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)



KNOWN_ASSESSMENTS = [
    {
        "name": "Automata Fix (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/automata-fix-new/",
        "description": "Coding test that measures ability to identify and fix bugs in code. Assesses debugging skills in a realistic coding environment.",
        "duration": 20,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Core Java (Entry Level) (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/core-java-entry-level-new/",
        "description": "Measures knowledge of Java programming for entry-level positions. Tests core Java concepts, OOP, and standard library usage.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Python (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/python-new/",
        "description": "Multi-choice test measuring knowledge of Python programming, databases, modules and library usage.",
        "duration": 11,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Technology Professional 8.0 Job Focused Assessment",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/technology-professional-8-0-job-focused-assessment/",
        "description": "Assesses key behavioural attributes required for success in fast-paced technology roles.",
        "duration": 16,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Competencies", "Personality & Behaviour"]
    },
    {
        "name": "Numerical Reasoning",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/numerical-reasoning/",
        "description": "Measures ability to interpret numerical data and make accurate decisions based on numerical information.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Verbal Reasoning",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/verbal-reasoning/",
        "description": "Assesses ability to evaluate verbal information and draw valid conclusions from written text.",
        "duration": 17,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Inductive Reasoning",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/inductive-reasoning/",
        "description": "Measures abstract reasoning ability and capacity to identify patterns and logical rules.",
        "duration": 24,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Occupational Personality Questionnaire (OPQ32)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/occupational-personality-questionnaire-opq32/",
        "description": "Measures 32 personality characteristics relevant to work performance. Provides insight into behaviour and preferred work style.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "Motivation Questionnaire (MQ)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/motivation-questionnaire-mq/",
        "description": "Assesses factors that increase or decrease motivation at work. Helps understand what energizes an individual.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "SQL (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sql-new/",
        "description": "Tests SQL knowledge including queries, joins, database design, and optimization for data-related roles.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "JavaScript (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/javascript-new/",
        "description": "Assesses knowledge of JavaScript programming including ES6+, DOM manipulation, and modern frameworks.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Deductive Reasoning",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/deductive-reasoning/",
        "description": "Measures ability to draw logical conclusions from given information and apply rules systematically.",
        "duration": 20,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Verify Numerical Ability",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-numerical-ability/",
        "description": "Short adaptive numerical reasoning test suitable for volume screening with high accuracy.",
        "duration": 18,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Verify Verbal Ability",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-verbal-ability/",
        "description": "Short adaptive verbal reasoning test measuring comprehension and logical reasoning with written material.",
        "duration": 18,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Workplace English Language Test (WELT)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/workplace-english-language-test/",
        "description": "Assesses English language proficiency in a workplace context including reading, writing, and comprehension.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "MQ Manager & Professional",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/mq-manager-professional/",
        "description": "Measures motivational preferences for managers and professionals. Identifies energy sources and potential derailers.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "Customer Service Scenarios",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/customer-service-scenarios/",
        "description": "Situational judgement test for customer-facing roles measuring problem solving and service orientation.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Biodata & Situational Judgement"]
    },
    {
        "name": "Financial Professional - Short Form",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/financial-professional-short-form/",
        "description": "Personality assessment specifically designed for financial services professionals.",
        "duration": 12,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "ADEPT-15",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/adept-15/",
        "description": "Adaptive personality assessment measuring 15 personality factors predictive of workplace performance.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "Sales Representative Solution",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sales-representative-solution/",
        "description": "Comprehensive assessment for sales roles measuring personality, cognitive ability, and sales-specific competencies.",
        "duration": 45,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour", "Ability & Aptitude"]
    },
    {
        "name": "General Ability - Short",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/general-ability-short/",
        "description": "Short assessment of general cognitive ability suitable for volume screening across all job levels.",
        "duration": 10,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Java (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/java-new/",
        "description": "Comprehensive Java knowledge test for experienced developers covering advanced OOP, frameworks, and best practices.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "R (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/r-new/",
        "description": "Tests knowledge of R programming for data science and statistical analysis roles.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "C# (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/c-sharp-new/",
        "description": "Assesses C# programming knowledge for .NET development roles including LINQ, async, and OOP concepts.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "C++ (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/c-plus-plus-new/",
        "description": "Tests C++ programming knowledge including memory management, STL, templates, and modern C++ standards.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "MS Access (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/ms-access-new/",
        "description": "Assesses proficiency with Microsoft Access database creation, queries, and report building.",
        "duration": 20,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "MS Excel (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/ms-excel-new/",
        "description": "Comprehensive Excel proficiency test covering formulas, pivot tables, data analysis, and advanced features.",
        "duration": 20,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "MS PowerPoint (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/ms-powerpoint-new/",
        "description": "Tests Microsoft PowerPoint knowledge including presentations, animations, templates, and design.",
        "duration": 20,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "MS Word (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/ms-word-new/",
        "description": "Assesses Microsoft Word proficiency for administrative and business roles.",
        "duration": 20,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Global Skills Assessment",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/global-skills-assessment/",
        "description": "Measures cross-cultural and global working competencies required for international business roles.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Competencies"]
    },
    {
        "name": "Graduate 8.0",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/graduate-8-0/",
        "description": "Assessment solution designed for graduate-level hiring measuring potential and work-relevant behaviours.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour", "Ability & Aptitude"]
    },
    {
        "name": "Situational Judgement Test - Operations",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/sjt-operations/",
        "description": "Situational judgement test for operations roles measuring decision making in realistic work scenarios.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Biodata & Situational Judgement"]
    },
    {
        "name": "Agile Software Developer (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/agile-software-developer-new/",
        "description": "Assesses Agile methodologies, Scrum practices, and software development knowledge for modern teams.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Entry Level Sales 7.1 (International)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/entry-level-sales-7-1-international/",
        "description": "Assessment for entry level sales candidates measuring customer orientation and commercial aptitude.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "Calculation",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/calculation/",
        "description": "Tests basic arithmetic calculation ability used for clerical and administrative screening.",
        "duration": 10,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Coding Simulation",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/coding-simulation/",
        "description": "Realistic coding simulation to assess software development skills through practical programming tasks.",
        "duration": 60,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Simulations", "Knowledge & Skills"]
    },
    {
        "name": "Universal Competency Framework (UCF)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/universal-competency-framework/",
        "description": "Behavioural competency framework for measuring leadership and management potential.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Competencies"]
    },
    {
        "name": "DevOps (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/devops-new/",
        "description": "Tests DevOps knowledge including CI/CD pipelines, containerization, infrastructure as code, and monitoring.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Data Analysis using Python (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/data-analysis-using-python-new/",
        "description": "Assesses data analysis skills using Python libraries including pandas, NumPy, and matplotlib.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "Machine Learning with Python (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/machine-learning-with-python-new/",
        "description": "Tests machine learning knowledge using Python scikit-learn and deep learning frameworks.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "AWS (New)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/aws-new/",
        "description": "Assesses Amazon Web Services knowledge including EC2, S3, Lambda, and cloud architecture patterns.",
        "duration": 20,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills"]
    },
    {
        "name": "General Reasoning Battery",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/general-reasoning-battery/",
        "description": "Comprehensive battery assessing verbal, numerical, and inductive reasoning for graduate and professional roles.",
        "duration": 60,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "Customer Contact Styles",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/customer-contact-styles/",
        "description": "Personality questionnaire for customer-facing roles measuring service orientation and communication style.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "Excel Simulation",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/excel-simulation/",
        "description": "Practical Excel simulation testing real-world spreadsheet tasks in an interactive environment.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Simulations", "Knowledge & Skills"]
    },
    {
        "name": "Contact Centre Scenarios",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/contact-centre-scenarios/",
        "description": "SJT-style assessment for contact centre roles testing customer handling and problem resolution skills.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Biodata & Situational Judgement"]
    },
    {
        "name": "Verify G+",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/verify-g-plus/",
        "description": "Short cognitive ability screener covering numerical, verbal, and deductive reasoning in one brief test.",
        "duration": 8,
        "remote_support": "Yes",
        "adaptive_support": "Yes",
        "test_types": ["Ability & Aptitude"]
    },
    {
        "name": "OPQ32r",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/opq32r/",
        "description": "Revised version of OPQ32 personality questionnaire with improved psychometric properties for professional use.",
        "duration": 25,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "Aspects Styles",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/aspects-styles/",
        "description": "Short personality questionnaire assessing key work-relevant personality characteristics for operational roles.",
        "duration": 15,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "TypeFocus Personality",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/typefocus-personality/",
        "description": "MBTI-aligned personality type assessment for career development and team building.",
        "duration": 30,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
    {
        "name": "Business Analyst",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/business-analyst/",
        "description": "Job-focused assessment for business analyst roles measuring analytical thinking and stakeholder communication.",
        "duration": 40,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Competencies", "Knowledge & Skills"]
    },
    {
        "name": "Project Manager Solution",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/project-manager-solution/",
        "description": "Comprehensive assessment for project management roles measuring PM knowledge and leadership competencies.",
        "duration": 45,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Knowledge & Skills", "Competencies"]
    },
    {
        "name": "Workplace Personality Inventory II (WPI II)",
        "url": "https://www.shl.com/solutions/products/product-catalog/view/workplace-personality-inventory-ii/",
        "description": "Comprehensive personality measure assessing work-relevant traits and predicting job performance.",
        "duration": 40,
        "remote_support": "Yes",
        "adaptive_support": "No",
        "test_types": ["Personality & Behaviour"]
    },
]




def generate(output_path: str = "data/assessments.json", min_count: int = 50):
    """Generate mock assessment data for testing."""
    from pathlib import Path
    import json

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(KNOWN_ASSESSMENTS, f, indent=2, ensure_ascii=False)

    print(f" Mock data written: {len(KNOWN_ASSESSMENTS)} assessments to {path}")
    print("⚠️ NOTE: This is MOCK data for testing only.")
    print("   Run crawler/shl_crawler.py for production (requires internet access)")
    return KNOWN_ASSESSMENTS


if __name__ == "__main__":
    generate()
