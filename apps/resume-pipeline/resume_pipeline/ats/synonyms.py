"""Tech synonym dictionary — maps aliases/abbreviations to canonical forms.

Design: canonical form → list of aliases.
At runtime we build a reverse map: alias → canonical.

Covers ~250 common tech terms across backend, frontend, cloud, data, and DevOps.
"""

# canonical_term -> [aliases, abbreviations, alternate spellings]
TECH_SYNONYMS: dict[str, list[str]] = {
    # Languages
    "javascript": ["js", "ecmascript", "es6", "es2015", "es2016", "es2017", "es2018", "es2019", "es2020"],
    "typescript": ["ts"],
    "python": ["py", "python3", "python2"],
    "java": [],
    "kotlin": [],
    "scala": [],
    "go": ["golang"],
    "rust": [],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp", "dotnet", "net"],
    "ruby": ["rb"],
    "swift": [],
    "objective-c": ["objc"],
    "php": [],
    "r": [],
    "matlab": [],
    "shell": ["bash", "sh", "zsh", "shell scripting"],
    "sql": ["structured query language"],
    "graphql": ["gql"],
    "html": ["html5"],
    "css": ["css3", "stylesheets"],
    "sass": ["scss"],

    # Frameworks / Libraries — Frontend
    "react": ["reactjs", "react.js", "react js"],
    "angular": ["angularjs", "angular.js", "angular js"],
    "vue": ["vuejs", "vue.js", "vue js"],
    "svelte": [],
    "next.js": ["nextjs", "next js"],
    "nuxt.js": ["nuxtjs", "nuxt js"],
    "redux": [],
    "mobx": [],
    "webpack": [],
    "vite": [],
    "tailwind": ["tailwind css", "tailwindcss"],
    "bootstrap": [],

    # Frameworks — Backend
    "spring boot": ["spring", "spring framework", "springboot"],
    "django": [],
    "flask": [],
    "fastapi": ["fast api"],
    "express": ["express.js", "expressjs"],
    "node.js": ["nodejs", "node js", "node"],
    "rails": ["ruby on rails", "ror"],
    "laravel": [],
    "gin": [],
    "fiber": [],
    "grpc": ["grpc"],
    "rest": ["restful", "rest api", "restful api", "rest apis", "restful apis"],
    "graphql": ["gql", "graph ql"],

    # Cloud — AWS
    "amazon web services": ["aws"],
    "ec2": ["amazon ec2"],
    "s3": ["amazon s3"],
    "lambda": ["aws lambda"],
    "rds": ["amazon rds"],
    "cloudfront": ["aws cloudfront"],
    "eks": ["amazon eks", "elastic kubernetes service"],
    "ecs": ["amazon ecs", "elastic container service"],
    "sqs": ["amazon sqs", "simple queue service"],
    "sns": ["amazon sns", "simple notification service"],
    "cloudwatch": ["aws cloudwatch"],
    "iam": ["aws iam"],
    "vpc": ["aws vpc"],
    "dynamodb": ["dynamo db", "amazon dynamodb"],
    "opensearch": ["aws opensearch", "amazon opensearch", "elasticsearch"],  # close enough for skills

    # Cloud — GCP
    "google cloud platform": ["gcp", "google cloud"],
    "bigquery": ["big query"],
    "cloud run": [],
    "gke": ["google kubernetes engine"],

    # Cloud — Azure
    "microsoft azure": ["azure"],
    "azure devops": [],
    "aks": ["azure kubernetes service"],

    # Databases
    "postgresql": ["postgres", "pg", "psql"],
    "mysql": [],
    "microsoft sql server": ["mssql", "sql server"],
    "oracle": ["oracle db", "oracle database"],
    "mongodb": ["mongo", "mongo db"],
    "cassandra": ["apache cassandra"],
    "redis": ["redis cache", "redis caching"],
    "memcached": ["memcache"],
    "couchbase": [],
    "dynamodb": ["dynamo", "dynamo db"],
    "firebase": ["firestore"],
    "sqlite": [],
    "neo4j": [],
    "elasticsearch": ["elastic search", "opensearch", "lucene"],
    "clickhouse": [],
    "snowflake": [],
    "databricks": [],

    # Messaging / Streaming
    "apache kafka": ["kafka"],
    "rabbitmq": ["rabbit mq", "amqp"],
    "apache pulsar": ["pulsar"],
    "nats": [],
    "activemq": ["active mq"],
    "amazon sqs": ["sqs"],

    # DevOps / Infrastructure
    "docker": ["containerization", "containers"],
    "kubernetes": ["k8s", "kube", "k8"],
    "terraform": ["tf"],
    "ansible": [],
    "helm": [],
    "jenkins": [],
    "github actions": ["gha"],
    "gitlab ci": ["gitlab ci/cd"],
    "circleci": ["circle ci"],
    "argocd": ["argo cd"],
    "prometheus": [],
    "grafana": [],
    "datadog": ["data dog"],
    "splunk": [],
    "elk stack": ["elasticsearch kibana logstash", "elk"],
    "nginx": [],
    "apache": ["apache httpd"],
    "vault": ["hashicorp vault"],
    "consul": ["hashicorp consul"],
    "istio": [],
    "linkerd": [],

    # CI/CD / Practices
    "ci/cd": ["cicd", "ci", "cd", "continuous integration", "continuous deployment",
               "continuous delivery", "continuous integration continuous deployment",
               "continuous integration continuous delivery"],
    "infrastructure as code": ["iac"],
    "gitops": ["git ops"],
    "agile": ["scrum", "agile development", "agile methodology"],
    "devops": ["dev ops"],
    "sre": ["site reliability engineering"],
    "tdd": ["test driven development", "test-driven development"],
    "bdd": ["behavior driven development"],

    # AI / ML
    "machine learning": ["ml"],
    "artificial intelligence": ["ai"],
    "natural language processing": ["nlp"],
    "large language model": ["llm", "llms"],
    "retrieval augmented generation": ["rag"],
    "langchain": ["lang chain"],
    "tensorflow": ["tf"],
    "pytorch": ["torch"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "openai": ["open ai", "chatgpt", "gpt"],
    "hugging face": ["huggingface"],

    # Auth / Security
    "oauth": ["oauth2", "oauth 2.0"],
    "jwt": ["json web token", "json web tokens"],
    "oidc": ["openid connect"],
    "okta": [],
    "auth0": ["auth 0"],
    "keycloak": [],
    "saml": [],
    "ssl": ["tls", "ssl/tls", "https"],

    # Methodologies / Patterns
    "microservices": ["micro services", "microservice architecture"],
    "service oriented architecture": ["soa"],
    "event driven": ["event-driven", "event driven architecture", "eda"],
    "distributed systems": ["distributed system"],
    "high availability": ["ha"],
    "fault tolerant": ["fault tolerance"],
    "api gateway": [],
    "backend for frontend": ["bff"],
    "caching": ["cache"],
    "load balancing": ["load balancer"],

    # Monitoring / Observability
    "observability": [],
    "distributed tracing": ["tracing", "opentelemetry", "otel", "jaeger", "zipkin"],
    "sla": ["service level agreement"],
    "slo": ["service level objective"],
    "sli": ["service level indicator"],

    # Testing
    "unit testing": ["unit test", "unit tests"],
    "integration testing": ["integration test"],
    "end to end testing": ["e2e", "e2e testing"],
    "junit": [],
    "pytest": [],
    "jest": [],
    "cypress": [],
    "postman": [],

    # Version Control
    "git": [],
    "github": [],
    "gitlab": [],
    "bitbucket": [],

    # Misc Tech
    "linux": ["unix"],
    "bash": ["shell", "shell scripting"],
    "regex": ["regular expressions", "regexp"],
    "json": [],
    "yaml": [],
    "xml": [],
    "protobuf": ["protocol buffers"],
    "grpc": ["grpc", "google rpc"],
    "websocket": ["websockets", "web socket"],
    "apache spark": ["spark", "pyspark"],
    "hadoop": ["apache hadoop"],
    "airflow": ["apache airflow"],
    "dbt": ["data build tool"],
}


def build_reverse_map() -> dict[str, str]:
    """Return alias → canonical mapping for fast lookup."""
    reverse: dict[str, str] = {}
    for canonical, aliases in TECH_SYNONYMS.items():
        reverse[canonical] = canonical
        for alias in aliases:
            reverse[alias.lower()] = canonical
    return reverse


# Module-level reverse map (built once on import)
ALIAS_TO_CANONICAL: dict[str, str] = build_reverse_map()


def normalise(term: str) -> str:
    """Return the canonical form of a tech term, or the original if unknown."""
    return ALIAS_TO_CANONICAL.get(term.lower().strip(), term.lower().strip())
