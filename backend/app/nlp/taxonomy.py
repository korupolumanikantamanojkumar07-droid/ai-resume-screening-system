import re
from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np

# Structured Skill Taxonomy with canonical names, categories, and synonyms/variations
DEFAULT_SKILL_TAXONOMY: list[dict] = [
    # Programming Languages
    {"name": "Python", "category": "Programming", "synonyms": ["python3", "py", "python programming"]},
    {"name": "Java", "category": "Programming", "synonyms": ["java8", "java 11", "java 17", "j2ee", "core java"]},
    {"name": "C++", "category": "Programming", "synonyms": ["cpp", "c plus plus"]},
    {"name": "C", "category": "Programming", "synonyms": ["c programming", "ansi c"]},
    {"name": "C#", "category": "Programming", "synonyms": ["csharp", "c sharp", ".net core", "dotnet"]},
    {"name": "JavaScript", "category": "Programming", "synonyms": ["js", "ecmascript", "es6", "es2015"]},
    {"name": "TypeScript", "category": "Programming", "synonyms": ["ts"]},
    {"name": "Go", "category": "Programming", "synonyms": ["golang"]},
    {"name": "Rust", "category": "Programming", "synonyms": ["rustlang"]},
    {"name": "PHP", "category": "Programming", "synonyms": ["php7", "php8", "laravel"]},
    {"name": "Ruby", "category": "Programming", "synonyms": ["ruby on rails", "ror"]},
    {"name": "Swift", "category": "Programming", "synonyms": ["swiftui", "ios swift"]},
    {"name": "Kotlin", "category": "Programming", "synonyms": ["android kotlin", "android sdk", "android studio"]},
    {"name": "Scala", "category": "Programming", "synonyms": []},
    {"name": "R", "category": "Programming", "synonyms": ["r programming", "r studio", "rstudio"]},
    {"name": "MATLAB", "category": "Programming", "synonyms": []},
    {"name": "Dart", "category": "Programming", "synonyms": ["flutter dart"]},
    {"name": "Bash", "category": "Programming", "synonyms": ["shell scripting", "bash scripting", "zsh"]},
    {"name": "Data Structures", "category": "Programming", "synonyms": ["algorithms", "dsa", "programming fundamentals"]},

    # AI / ML
    {"name": "Machine Learning", "category": "AI/ML", "synonyms": ["ml", "supervised learning", "unsupervised learning", "predictive modeling"]},
    {"name": "Deep Learning", "category": "AI/ML", "synonyms": ["dl", "neural networks", "cnn", "rnn", "lstm", "ann"]},
    {"name": "NLP", "category": "AI/ML", "synonyms": ["natural language processing", "text mining", "text analytics", "named entity recognition", "ner"]},
    {"name": "Computer Vision", "category": "AI/ML", "synonyms": ["cv", "image processing", "object detection", "yolo"]},
    {"name": "TensorFlow", "category": "AI/ML", "synonyms": ["tf", "tensorflow 2"]},
    {"name": "PyTorch", "category": "AI/ML", "synonyms": ["torch"]},
    {"name": "Keras", "category": "AI/ML", "synonyms": []},
    {"name": "Scikit-learn", "category": "AI/ML", "synonyms": ["sklearn", "scikit learn"]},
    {"name": "spaCy", "category": "AI/ML", "synonyms": ["spacy nlp"]},
    {"name": "NLTK", "category": "AI/ML", "synonyms": ["natural language toolkit"]},
    {"name": "Hugging Face", "category": "AI/ML", "synonyms": ["huggingface", "transformers", "sentence transformers", "bert"]},
    {"name": "LLM", "category": "AI/ML", "synonyms": ["large language models", "generative ai", "genai", "openai", "gpt", "rag", "langchain"]},
    {"name": "XGBoost", "category": "AI/ML", "synonyms": ["gradient boosting", "lightgbm", "catboost"]},
    {"name": "OpenCV", "category": "AI/ML", "synonyms": ["cv2"]},
    {"name": "Reinforcement Learning", "category": "AI/ML", "synonyms": ["rl", "q-learning"]},

    # Data & Analytics
    {"name": "SQL", "category": "Data", "synonyms": ["structured query language", "tsql", "pl/sql", "plsql"]},
    {"name": "Power BI", "category": "Data", "synonyms": ["powerbi", "microsoft power bi", "dax"]},
    {"name": "Tableau", "category": "Data", "synonyms": ["tableau desktop", "tableau server"]},
    {"name": "Excel", "category": "Data", "synonyms": ["microsoft excel", "ms excel", "advanced excel", "vba"]},
    {"name": "Pandas", "category": "Data", "synonyms": ["python pandas"]},
    {"name": "NumPy", "category": "Data", "synonyms": ["numpy"]},
    {"name": "SciPy", "category": "Data", "synonyms": []},
    {"name": "Apache Spark", "category": "Data", "synonyms": ["pyspark", "spark"]},
    {"name": "Hadoop", "category": "Data", "synonyms": ["hdfs", "mapreduce"]},
    {"name": "Apache Kafka", "category": "Data", "synonyms": ["kafka"]},
    {"name": "Apache Airflow", "category": "Data", "synonyms": ["airflow"]},
    {"name": "ETL", "category": "Data", "synonyms": ["extract transform load", "data pipeline", "data engineering", "data cleaning", "data preparation"]},
    {"name": "Data Visualization", "category": "Data", "synonyms": ["data visualisation", "dashboarding", "matplotlib", "seaborn", "plotly", "recharts", "d3.js"]},
    {"name": "Statistics", "category": "Data", "synonyms": ["statistical analysis", "hypothesis testing", "probability", "a/b testing", "eda", "exploratory data analysis", "model evaluation"]},
    {"name": "Snowflake", "category": "Data", "synonyms": []},
    {"name": "BigQuery", "category": "Data", "synonyms": ["google bigquery"]},

    # Web & App Development
    {"name": "HTML", "category": "Web", "synonyms": ["html5"]},
    {"name": "CSS", "category": "Web", "synonyms": ["css3", "scss", "sass"]},
    {"name": "React", "category": "Web", "synonyms": ["react.js", "reactjs", "react js"]},
    {"name": "Next.js", "category": "Web", "synonyms": ["nextjs"]},
    {"name": "Angular", "category": "Web", "synonyms": ["angularjs"]},
    {"name": "Vue.js", "category": "Web", "synonyms": ["vuejs", "vue"]},
    {"name": "Node.js", "category": "Web", "synonyms": ["nodejs", "node js"]},
    {"name": "Express.js", "category": "Web", "synonyms": ["expressjs", "express"]},
    {"name": "FastAPI", "category": "Web", "synonyms": ["fast api"]},
    {"name": "Django", "category": "Web", "synonyms": ["django rest framework", "drf"]},
    {"name": "Flask", "category": "Web", "synonyms": []},
    {"name": "Spring Boot", "category": "Web", "synonyms": ["spring", "spring mvc"]},
    {"name": "Tailwind CSS", "category": "Web", "synonyms": ["tailwindcss", "tailwind"]},
    {"name": "REST API", "category": "Web", "synonyms": ["restful api", "rest apis", "restful services", "web api"]},
    {"name": "GraphQL", "category": "Web", "synonyms": []},
    {"name": "Flutter", "category": "Web", "synonyms": ["flutter sdk"]},
    {"name": "WordPress", "category": "Web", "synonyms": ["wp", "woocommerce"]},

    # Cloud & DevOps
    {"name": "AWS", "category": "Cloud", "synonyms": ["amazon web services", "ec2", "s3", "aws lambda", "sagemaker"]},
    {"name": "Azure", "category": "Cloud", "synonyms": ["microsoft azure", "azure ml", "azure devops"]},
    {"name": "Google Cloud", "category": "Cloud", "synonyms": ["gcp", "google cloud platform"]},
    {"name": "Docker", "category": "DevOps", "synonyms": ["docker compose", "containerization"]},
    {"name": "Kubernetes", "category": "DevOps", "synonyms": ["k8s"]},
    {"name": "Terraform", "category": "DevOps", "synonyms": ["infrastructure as code", "iac"]},
    {"name": "CI/CD", "category": "DevOps", "synonyms": ["github actions", "jenkins", "gitlab ci", "continuous integration"]},
    {"name": "Linux", "category": "DevOps", "synonyms": ["ubuntu", "centos", "unix"]},
    {"name": "Git", "category": "DevOps", "synonyms": ["github", "gitlab", "bitbucket", "version control"]},
    {"name": "Nginx", "category": "DevOps", "synonyms": ["apache http"]},

    # Databases
    {"name": "PostgreSQL", "category": "Database", "synonyms": ["postgres"]},
    {"name": "MySQL", "category": "Database", "synonyms": []},
    {"name": "MongoDB", "category": "Database", "synonyms": ["mongo", "nosql"]},
    {"name": "Redis", "category": "Database", "synonyms": []},
    {"name": "SQLite", "category": "Database", "synonyms": []},
    {"name": "Oracle", "category": "Database", "synonyms": ["oracle db"]},
    {"name": "Elasticsearch", "category": "Database", "synonyms": ["elk stack"]},

    # Soft & Professional Skills
    {"name": "Communication", "category": "Soft Skills", "synonyms": ["verbal communication", "written communication", "presentation skills"]},
    {"name": "Leadership", "category": "Soft Skills", "synonyms": ["team leadership", "people management", "mentoring"]},
    {"name": "Problem Solving", "category": "Soft Skills", "synonyms": ["analytical thinking", "troubleshooting", "debugging"]},
    {"name": "Team Collaboration", "category": "Soft Skills", "synonyms": ["teamwork", "cross-functional collaboration"]},
    {"name": "Agile", "category": "Soft Skills", "synonyms": ["scrum", "kanban", "sprint planning"]},
    {"name": "Project Management", "category": "Soft Skills", "synonyms": ["jira", "stakeholder management", "product management"]},
    {"name": "System Design", "category": "Domain", "synonyms": ["microservices", "distributed systems", "software architecture"]},
    {"name": "Cybersecurity", "category": "Domain", "synonyms": ["network security", "information security", "owasp", "penetration testing", "wireshark", "vulnerability assessment", "siem"]},
    {"name": "Networking", "category": "Domain", "synonyms": ["computer networks", "tcp/ip", "dns"]},
    {"name": "Unit Testing", "category": "Domain", "synonyms": ["pytest", "junit", "jest", "automated testing", "testing", "qa"]},
    {"name": "UI/UX Design", "category": "Domain", "synonyms": ["figma", "wireframing", "prototyping", "usability testing", "accessibility"]},
    {"name": "Firebase", "category": "Database", "synonyms": ["cloud firestore"]},
    {"name": "Monitoring", "category": "DevOps", "synonyms": ["observability", "prometheus", "grafana"]},
]

# Contextual descriptions for semantic skill inference when exact keywords are absent
SKILL_SEMANTIC_DESCRIPTIONS: dict[str, str] = {
    "Machine Learning": "predictive modeling supervised classification regression feature engineering model training",
    "Deep Learning": "convolutional neural networks transformers backpropagation training deep architectures",
    "NLP": "text classification tokenization named entity recognition sentiment analysis language modeling",
    "Computer Vision": "image classification object detection segmentation visual recognition",
    "Data Visualization": "interactive dashboards charts visual analytics reporting metrics",
    "ETL": "data ingestion extraction transformation loading pipelines warehouse automation",
    "REST API": "http endpoints backend api design json request response services",
    "CI/CD": "automated build test deployment pipelines release automation",
    "System Design": "scalable distributed backend architecture microservices high availability",
    "Cloud": "cloud infrastructure deployment serverless storage compute scaling",
    "Project Management": "sprint planning roadmap stakeholder coordination delivery tracking",
    "Leadership": "leading engineering teams mentoring junior developers technical direction",
}


@dataclass
class ExtractedSkillMatch:
    name: str
    category: str
    match_method: str  # exact | synonym | semantic
    confidence: float


def _build_boundary_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term.lower())
    # Special handling for short or symbol-heavy tokens like C, R, C++, C#
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


def normalize_skill_name(skill_text: str, taxonomy: Optional[list[dict]] = None) -> str:
    """Normalize a raw skill or synonym string into its canonical taxonomy name if known."""
    items = taxonomy or DEFAULT_SKILL_TAXONOMY
    cleaned = skill_text.strip().lower()
    for item in items:
        if item["name"].lower() == cleaned:
            return item["name"]
        for syn in item.get("synonyms", []):
            if syn.lower() == cleaned:
                return item["name"]
    return skill_text.strip()


def extract_skills_from_text(
    text: str,
    taxonomy: Optional[list[dict]] = None,
    sentences: Optional[list[str]] = None,
    embed_fn=None,
    enable_semantic: bool = True,
) -> list[ExtractedSkillMatch]:
    """
    Identify skills via 3 complementary NLP methods:
    1. Canonical boundary-aware matching
    2. Synonym/variation matching (e.g., 'ML' -> 'Machine Learning', 'Natural Language Processing' -> 'NLP')
    3. Semantic phrase similarity using SentenceTransformer embeddings (if embed_fn provided)
    """
    items = taxonomy or DEFAULT_SKILL_TAXONOMY
    if not text:
        return []

    matches: dict[str, ExtractedSkillMatch] = {}

    for item in items:
        canonical = item["name"]
        category = item["category"]
        # 1. Exact canonical match
        if _build_boundary_pattern(canonical).search(text):
            matches[canonical] = ExtractedSkillMatch(
                name=canonical, category=category, match_method="exact", confidence=1.0
            )
            continue

        # 2. Synonym / variation match
        for syn in item.get("synonyms", []):
            if not syn or len(syn.strip()) < 2:
                continue
            if _build_boundary_pattern(syn).search(text):
                matches[canonical] = ExtractedSkillMatch(
                    name=canonical, category=category, match_method="synonym", confidence=0.95
                )
                break

    # 3. Semantic skill inference for unmatched conceptual skills
    if enable_semantic and embed_fn is not None and sentences:
        candidate_sents = [s for s in sentences if 20 <= len(s) <= 320][:25]
        if candidate_sents:
            unmatched_items = [
                item for item in items
                if item["name"] not in matches and item["name"] in SKILL_SEMANTIC_DESCRIPTIONS
            ]
            if unmatched_items:
                sent_vecs = embed_fn(candidate_sents)
                desc_texts = [
                    f"{item['name']} {SKILL_SEMANTIC_DESCRIPTIONS[item['name']]}"
                    for item in unmatched_items
                ]
                desc_vecs = embed_fn(desc_texts)
                # Cosine similarity (embeddings are L2-normalized)
                sim_matrix = np.matmul(desc_vecs, sent_vecs.T)
                for idx, item in enumerate(unmatched_items):
                    max_sim = float(np.max(sim_matrix[idx]))
                    if max_sim >= 0.50:
                        matches[item["name"]] = ExtractedSkillMatch(
                            name=item["name"],
                            category=item["category"],
                            match_method="semantic",
                            confidence=round(min(0.89, max_sim), 3),
                        )

    return sorted(matches.values(), key=lambda m: (-m.confidence, m.name))
