"""
Search Result Fetcher
- Demo mode: query-aware topic corpus (returns relevant results, not fixed ML content)
- Live mode: DuckDuckGo HTML scraping with improved parser
"""

import requests
import re
import random
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Topic Corpora ──────────────────────────────────────────────────────────────
# Each topic has realistic results. get_demo_results() picks the right one
# based on query keywords so re-ranking demonstrates real value.

TOPIC_CORPORA = {

    "ai_tools": [
        {
            "title": "Midjourney — AI Image Generator for Artists and Designers",
            "url": "https://www.midjourney.com",
            "snippet": "Midjourney is an AI image generation tool that creates stunning, high-quality artwork from text prompts. Popular among digital artists, designers, and creators. Subscription plans start at $10/month with a free trial available.",
        },
        {
            "title": "DALL-E 3 by OpenAI — Generate Images from Text (Free with ChatGPT)",
            "url": "https://openai.com/dall-e-3",
            "snippet": "DALL-E 3 is OpenAI's most capable image generation model. Generate detailed, accurate images from natural language descriptions. Available free through ChatGPT and via API. Updated 2025 with improved photorealism.",
        },
        {
            "title": "Stable Diffusion — Free Open Source AI Image Generation",
            "url": "https://stability.ai/stable-diffusion",
            "snippet": "Stable Diffusion is a free, open-source AI image generation model you can run locally on your own computer. No subscription needed. Supports thousands of community models for photorealistic images, anime, art styles, and more.",
        },
        {
            "title": "Adobe Firefly — AI Image Generation Built Into Creative Cloud",
            "url": "https://www.adobe.com/products/firefly.html",
            "snippet": "Adobe Firefly integrates AI image generation directly into Photoshop, Illustrator, and Express. Commercially safe AI trained on licensed content. Generate images, remove backgrounds, extend photos, and more. Free tier available.",
        },
        {
            "title": "Bing Image Creator — Free AI Art Generator by Microsoft (DALL-E Powered)",
            "url": "https://www.bing.com/create",
            "snippet": "Bing Image Creator is completely free and powered by DALL-E. Generate AI images from text descriptions with no subscription required. Sign in with a Microsoft account to get started. Creates 4 images per prompt.",
        },
        {
            "title": "Leonardo AI — Professional AI Image Generation Platform",
            "url": "https://leonardo.ai",
            "snippet": "Leonardo AI is a powerful AI image generation platform used by game developers, artists, and marketers. Offers fine-tuned models for consistent character generation, product images, and concept art. Free plan available with 150 tokens/day.",
        },
        {
            "title": "Canva AI Image Generator — Free AI Art Tool for Everyone",
            "url": "https://www.canva.com/ai-image-generator",
            "snippet": "Canva's built-in AI image generator lets you create stunning visuals directly in your designs. No design experience needed. Free to use with a Canva account. Supports text-to-image, background generation, and image editing with AI.",
        },
        {
            "title": "Runway ML — AI Video and Image Generation for Creators",
            "url": "https://runwayml.com",
            "snippet": "Runway ML offers AI-powered image and video generation tools for filmmakers, artists, and content creators. Gen-2 model creates videos from text or images. Used by major studios. Free trial available with 125 credits.",
        },
        {
            "title": "Ideogram — Free AI Image Generator with Excellent Text Rendering",
            "url": "https://ideogram.ai",
            "snippet": "Ideogram is a free AI image generation tool that excels at rendering accurate text within images — a weakness of most AI art tools. Perfect for posters, logos, and banners. Free tier generates 10 images/day. Updated 2025.",
        },
        {
            "title": "Google ImageFX — Free AI Image Generator by Google (Imagen 3)",
            "url": "https://labs.google/fx/tools/image-fx",
            "snippet": "Google's ImageFX is powered by Imagen 3, one of the highest-quality AI image generation models available. Completely free to use with a Google account. Generates photorealistic images, illustrations, and abstract art from text prompts.",
        },
        {
            "title": "Playground AI — Free Online AI Image Generator with No Daily Limits",
            "url": "https://playground.com",
            "snippet": "Playground AI offers a generous free tier for AI image generation with no strict daily limits. Supports multiple models including Stable Diffusion and DALL-E. Great for beginners and professionals alike. Create, remix, and edit images online.",
        },
        {
            "title": "Futurepedia — The Largest Directory of Free AI Tools 2025",
            "url": "https://www.futurepedia.io",
            "snippet": "Futurepedia is the largest AI tools directory with 5000+ AI tools across all categories. Find the best free AI image generators, writing assistants, video tools, and more. Updated daily with new tools. Filter by price, category, and use case.",
        },
    ],

    "coding": [
        {
            "title": "Stack Overflow — Programming Q&A for Developers",
            "url": "https://stackoverflow.com",
            "snippet": "Stack Overflow is the world's largest developer community with 58 million answers to programming questions. Search for solutions to Python, JavaScript, SQL errors and more. Free to use, with answers vetted by millions of developers.",
        },
        {
            "title": "GitHub — Where the World Builds Software",
            "url": "https://github.com",
            "snippet": "GitHub hosts over 420 million open-source repositories. Find code examples, libraries, frameworks, and tools for every programming language. Fork, star, and collaborate on projects. GitHub Copilot provides AI-powered code suggestions.",
        },
        {
            "title": "MDN Web Docs — JavaScript, CSS, HTML Reference",
            "url": "https://developer.mozilla.org",
            "snippet": "MDN Web Docs is the most comprehensive reference for web technologies. Complete documentation for HTML, CSS, JavaScript, Web APIs, and browser compatibility data. Maintained by Mozilla and used by millions of developers worldwide.",
        },
        {
            "title": "freeCodeCamp — Learn to Code for Free (Python, JavaScript, React)",
            "url": "https://www.freecodecamp.org",
            "snippet": "freeCodeCamp offers 3000+ hours of free coding tutorials, projects, and certifications. Learn Python, JavaScript, React, Node.js, SQL, and more. Used by 10 million learners. Includes hands-on projects and a supportive developer community.",
        },
        {
            "title": "Real Python — Python Tutorials for Developers of All Skill Levels",
            "url": "https://realpython.com",
            "snippet": "Real Python publishes in-depth Python tutorials, best practices, and courses. Topics include web development with Flask/Django, data science, automation, testing, and Python best practices. Both free articles and paid courses available.",
        },
        {
            "title": "GeeksforGeeks — DSA, Algorithms, Coding Interview Prep",
            "url": "https://www.geeksforgeeks.org",
            "snippet": "GeeksforGeeks covers data structures, algorithms, programming languages, and interview preparation. Includes 80,000+ programming articles, practice problems, and coding challenges. Popular for technical interview prep at Google, Amazon, Microsoft.",
        },
        {
            "title": "Dev.to — Community for Software Developers to Share and Learn",
            "url": "https://dev.to",
            "snippet": "Dev.to is a community of software developers sharing articles, tutorials, and discussions. Find tutorials on Python, JavaScript, Docker, AWS, and more. Active community with 1 million+ members. Great for learning modern development practices.",
        },
        {
            "title": "Python.org Official Documentation — Python 3.12 Reference",
            "url": "https://docs.python.org/3",
            "snippet": "The official Python 3 documentation covering all built-in functions, standard library modules, and language reference. Includes tutorial for beginners, library reference, and how-to guides. Essential bookmark for every Python developer.",
        },
        {
            "title": "W3Schools — Web Development Tutorials and Reference",
            "url": "https://www.w3schools.com",
            "snippet": "W3Schools provides free tutorials on HTML, CSS, JavaScript, Python, SQL, PHP, and more. Beginner-friendly with interactive examples and a built-in code editor. Trusted by millions of learners. Includes certifications for web technologies.",
        },
        {
            "title": "Codecademy — Interactive Coding Lessons and Career Paths",
            "url": "https://www.codecademy.com",
            "snippet": "Codecademy offers interactive coding lessons in 14 programming languages including Python, JavaScript, SQL, and R. Hands-on projects, career paths, and skill assessments. Free and Pro plans available. Learn at your own pace.",
        },
        {
            "title": "LeetCode — Practice Coding Problems for Technical Interviews",
            "url": "https://leetcode.com",
            "snippet": "LeetCode has 3000+ coding problems used in technical interviews at top tech companies. Practice algorithms, data structures, and system design. Used by engineers at Google, Meta, Amazon. Free and premium tiers available.",
        },
        {
            "title": "DigitalOcean Tutorials — Cloud, DevOps and Programming Guides",
            "url": "https://www.digitalocean.com/community/tutorials",
            "snippet": "DigitalOcean's community tutorials cover Linux, Python, Node.js, Docker, Kubernetes, and cloud deployment. Step-by-step guides for real-world projects. Free to read, written and reviewed by developers.",
        },
    ],

    "medical": [
        {
            "title": "Mayo Clinic — Symptoms, Causes and Treatments",
            "url": "https://www.mayoclinic.org",
            "snippet": "Mayo Clinic provides trusted, expert medical information on diseases, symptoms, tests, and treatments. Written by physicians and medical staff. Covers conditions from common cold to rare diseases. Used by millions for health decisions.",
        },
        {
            "title": "WebMD — Medical Information and Health Advice",
            "url": "https://www.webmd.com",
            "snippet": "WebMD is one of the most visited health information websites. Find comprehensive information on symptoms, diseases, medications, and healthy living. Symptom checker tool helps identify potential conditions. Reviewed by board-certified physicians.",
        },
        {
            "title": "NIH MedlinePlus — Health Information from the National Library of Medicine",
            "url": "https://medlineplus.gov",
            "snippet": "MedlinePlus is the National Institutes of Health's free, authoritative health information resource. Covers 1000+ diseases and conditions, medications, lab tests, and medical videos. Written in plain language for patients and families.",
        },
        {
            "title": "Healthline — Evidence-Based Health Information",
            "url": "https://www.healthline.com",
            "snippet": "Healthline provides evidence-based health and wellness content reviewed by medical professionals. Covers nutrition, mental health, chronic conditions, medications, and fitness. Articles cite peer-reviewed research and clinical guidelines.",
        },
        {
            "title": "Cleveland Clinic — Health Library and Medical Information",
            "url": "https://my.clevelandclinic.org/health",
            "snippet": "Cleveland Clinic's Health Library provides expert medical information reviewed by Cleveland Clinic physicians. Covers symptoms, diseases, treatments, drugs, and medical procedures. One of the top-ranked hospitals in the United States.",
        },
        {
            "title": "CDC — Disease Control, Vaccines and Public Health Guidelines",
            "url": "https://www.cdc.gov",
            "snippet": "The Centers for Disease Control and Prevention provides authoritative public health information on diseases, vaccines, outbreaks, and safety guidelines. Includes travel health advisories, COVID-19 updates, and chronic disease statistics.",
        },
        {
            "title": "PubMed — Biomedical Literature Database with 36 Million Citations",
            "url": "https://pubmed.ncbi.nlm.nih.gov",
            "snippet": "PubMed is the free, comprehensive biomedical literature database maintained by the National Library of Medicine. Access 36 million citations and abstracts from medical journals. Essential for evidence-based medicine and clinical research.",
        },
        {
            "title": "WHO — World Health Organization Global Health Guidelines",
            "url": "https://www.who.int",
            "snippet": "The World Health Organization provides global health data, clinical guidelines, and disease outbreak information. Covers infectious diseases, non-communicable diseases, mental health, and global health statistics. Authoritative international source.",
        },
        {
            "title": "Drugs.com — Medication Guide and Drug Interaction Checker",
            "url": "https://www.drugs.com",
            "snippet": "Drugs.com provides comprehensive prescription and over-the-counter medication information including dosage, side effects, warnings, and drug interaction checker. Covers 24,000+ medications. Written by pharmacists and reviewed for accuracy.",
        },
        {
            "title": "Medical News Today — Latest Health and Medical Research News",
            "url": "https://www.medicalnewstoday.com",
            "snippet": "Medical News Today reports on the latest health research, medical breakthroughs, and clinical findings. All articles reviewed by medical experts. Covers cardiology, oncology, neurology, mental health, and nutrition research.",
        },
    ],

    "research": [
        {
            "title": "arXiv.org — Open Access Preprint Server for Science and Engineering",
            "url": "https://arxiv.org",
            "snippet": "arXiv hosts 2.3 million open-access research papers in physics, mathematics, computer science, AI, statistics, and biology. Papers are freely available before peer review. The primary venue for sharing AI and ML research findings.",
        },
        {
            "title": "Google Scholar — Search Academic Papers, Theses and Citations",
            "url": "https://scholar.google.com",
            "snippet": "Google Scholar searches across academic journals, conference papers, theses, books, and preprints. Find citation counts, related works, and full-text links. Free access to millions of academic papers. Track author citations and h-index.",
        },
        {
            "title": "Semantic Scholar — AI-Powered Academic Search Engine",
            "url": "https://www.semanticscholar.org",
            "snippet": "Semantic Scholar is a free AI-powered research discovery tool covering 220 million academic papers. Uses machine learning to find key papers, extract insights, and show citation context. Particularly strong for computer science and biomedical research.",
        },
        {
            "title": "IEEE Xplore — Engineering and Technology Research Database",
            "url": "https://ieeexplore.ieee.org",
            "snippet": "IEEE Xplore is the premier database for electrical engineering, computer science, and electronics research. Access 5 million papers, standards, and conference proceedings from IEEE and IET. Authoritative source for technical and applied research.",
        },
        {
            "title": "ACM Digital Library — Computer Science Research Repository",
            "url": "https://dl.acm.org",
            "snippet": "The ACM Digital Library is the most comprehensive collection of computing and information technology research. Access papers from all ACM publications, conferences, and magazines including CACM, PLDI, and CHI.",
        },
        {
            "title": "ResearchGate — Connect with Researchers and Access Full-Text Papers",
            "url": "https://www.researchgate.net",
            "snippet": "ResearchGate is a social network for scientists with 20+ million members. Access full-text research papers, ask questions, and collaborate with researchers worldwide. Many authors share their papers freely on ResearchGate.",
        },
        {
            "title": "Papers With Code — Machine Learning Papers with Implementation Code",
            "url": "https://paperswithcode.com",
            "snippet": "Papers With Code links ML research papers to their open-source implementations and benchmarks. Track state-of-the-art results across 3000+ tasks. Essential for researchers who want to reproduce experiments or build on published work.",
        },
        {
            "title": "Nature — Peer-Reviewed Scientific Journal with High-Impact Research",
            "url": "https://www.nature.com",
            "snippet": "Nature is one of the world's most prestigious scientific journals. Publishes landmark research across biology, physics, chemistry, and earth sciences. High impact factor with rigorous peer review. Some articles freely accessible.",
        },
        {
            "title": "NCBI — National Center for Biotechnology Information Research Database",
            "url": "https://www.ncbi.nlm.nih.gov",
            "snippet": "NCBI provides free access to biomedical and genomic information including PubMed, GenBank, and clinical databases. Essential for life sciences research, bioinformatics, and medical literature searches.",
        },
        {
            "title": "Hugging Face — Open Source AI Models, Datasets and Papers",
            "url": "https://huggingface.co",
            "snippet": "Hugging Face hosts 400,000+ open source AI models and 150,000+ datasets. The go-to platform for NLP, computer vision, and multimodal AI research. Papers, demos, and code all in one place. Free to use and contribute.",
        },
    ],

    "news": [
        {
            "title": "Reuters — Breaking News, Latest Headlines and Live Updates",
            "url": "https://www.reuters.com",
            "snippet": "Reuters is one of the world's largest news agencies providing breaking news, business, financial, and political coverage. Trusted for accurate, unbiased reporting. Live updates on global events, markets, and technology news.",
        },
        {
            "title": "BBC News — World News, Analysis and Live Coverage",
            "url": "https://www.bbc.com/news",
            "snippet": "BBC News delivers trusted, impartial world news coverage with reporting from over 40 countries. Covers politics, business, technology, science, and culture. Available 24/7 with live streaming, video reports, and in-depth analysis.",
        },
        {
            "title": "TechCrunch — Technology News, Startup News and Analysis",
            "url": "https://techcrunch.com",
            "snippet": "TechCrunch covers the latest technology news, startup launches, funding rounds, and product announcements. Expert analysis on AI, social media, enterprise tech, and venture capital. Updated continuously with breaking tech news.",
        },
        {
            "title": "The Guardian — Independent News and Investigative Journalism",
            "url": "https://www.theguardian.com",
            "snippet": "The Guardian provides independent, investigative journalism on global politics, climate, social justice, and culture. Free to read with reader-supported funding model. Covers breaking news with in-depth analysis and opinion pieces.",
        },
        {
            "title": "Bloomberg — Business and Financial News, Market Data",
            "url": "https://www.bloomberg.com",
            "snippet": "Bloomberg is the leading source for business and financial news, market data, and economic analysis. Covers global markets, company earnings, mergers, and economic policy. Real-time data for stocks, bonds, commodities, and currencies.",
        },
        {
            "title": "The Verge — Technology, Science and Culture News",
            "url": "https://www.theverge.com",
            "snippet": "The Verge covers the intersection of technology, science, art, and culture. Known for in-depth product reviews, tech news, and analysis of how technology shapes modern life. Covers AI, smartphones, gaming, and streaming.",
        },
        {
            "title": "Associated Press — Trusted Global News Wire Service",
            "url": "https://apnews.com",
            "snippet": "The Associated Press is an independent, not-for-profit news cooperative trusted for fact-based journalism. Provides global news coverage in multiple languages. AP Fact Check debunks misinformation and verifies viral claims.",
        },
        {
            "title": "Hacker News — Tech Community News, Links and Discussion",
            "url": "https://news.ycombinator.com",
            "snippet": "Hacker News is Y Combinator's community for technology, startups, and science news. Curated links and discussions from the tech community. Covers programming, AI research, startup launches, and open source projects. Updated in real time.",
        },
        {
            "title": "Wired — In-Depth Technology and Science News",
            "url": "https://www.wired.com",
            "snippet": "Wired covers how technology transforms business, culture, and society. Known for long-form journalism on AI, cybersecurity, space exploration, and the future. Features interviews with tech leaders and investigative tech reporting.",
        },
        {
            "title": "MIT Technology Review — AI and Emerging Technology Analysis",
            "url": "https://www.technologyreview.com",
            "snippet": "MIT Technology Review provides authoritative coverage of emerging technologies including AI, biotech, climate tech, and computing. Expert analysis from MIT's research community. Essential reading for understanding technology's future impact.",
        },
    ],

    "legal": [
        {
            "title": "Cornell Law School — Legal Information Institute (LII)",
            "url": "https://www.law.cornell.edu",
            "snippet": "Cornell's Legal Information Institute provides free access to US law including the Constitution, US Code, Supreme Court decisions, and Code of Federal Regulations. Authoritative, freely accessible legal reference for everyone.",
        },
        {
            "title": "Justia — Free Case Law, Legal Research and Attorney Directory",
            "url": "https://www.justia.com",
            "snippet": "Justia provides free access to federal and state case law, statutes, regulations, and legal guides. Search Supreme Court opinions, circuit court decisions, and state appellate cases. Also offers a nationwide attorney directory.",
        },
        {
            "title": "FindLaw — Legal Information, Lawyer Directory and Law Blog",
            "url": "https://www.findlaw.com",
            "snippet": "FindLaw offers comprehensive legal information for consumers and professionals. Covers criminal law, family law, employment law, personal injury, and business law. Includes state-specific legal guides and free attorney consultations.",
        },
        {
            "title": "Nolo — Plain-English Legal Guides and DIY Legal Resources",
            "url": "https://www.nolo.com",
            "snippet": "Nolo publishes plain-English legal guides, forms, and software to help people handle legal matters without a lawyer. Topics include wills, contracts, landlord-tenant law, bankruptcy, and small business law. Trusted since 1971.",
        },
        {
            "title": "SCOTUS Blog — Supreme Court Coverage and Case Analysis",
            "url": "https://www.scotusblog.com",
            "snippet": "SCOTUSblog is the most comprehensive resource for US Supreme Court news, case analysis, and oral argument coverage. Tracks every cert petition and opinion. Used by lawyers, journalists, and legal scholars nationwide.",
        },
        {
            "title": "Oyez — Supreme Court Case Oral Arguments and Decisions",
            "url": "https://www.oyez.org",
            "snippet": "Oyez is a free online archive of US Supreme Court oral arguments, decisions, and case summaries going back to 1955. Listen to actual audio recordings. Comprehensive case summaries written by legal experts. Run by IIT Chicago-Kent.",
        },
        {
            "title": "Avvo — Lawyer Reviews, Legal Advice and Attorney Ratings",
            "url": "https://www.avvo.com",
            "snippet": "Avvo helps you find and evaluate lawyers with peer reviews, client ratings, and disciplinary history. Get free legal advice from licensed attorneys. Search by practice area and location. Covers criminal defense, family, immigration, and more.",
        },
        {
            "title": "USCourts.gov — Federal Judiciary Official Site and Court Records",
            "url": "https://www.uscourts.gov",
            "snippet": "The official website of the US federal court system. Access court records through PACER, find court locations, and read about federal court rules and procedures. Includes information on jury duty, federal bankruptcy, and court statistics.",
        },
        {
            "title": "LegalZoom — Online Legal Services and Document Preparation",
            "url": "https://www.legalzoom.com",
            "snippet": "LegalZoom provides affordable online legal services including LLC formation, trademark registration, wills, and contracts. Attorney-reviewed documents and optional consultation with licensed attorneys. Used by 4 million businesses.",
        },
        {
            "title": "Court Listener — Free Law Project — Open Legal Database",
            "url": "https://www.courtlistener.com",
            "snippet": "CourtListener is a free, open legal research platform with 8 million court opinions from all US federal and many state courts. Search by case name, citation, judge, or keyword. Part of the Free Law Project open-source initiative.",
        },
    ],

    "business": [
        {
            "title": "Harvard Business Review — Management and Business Strategy",
            "url": "https://hbr.org",
            "snippet": "Harvard Business Review publishes cutting-edge research on leadership, strategy, innovation, and management. Articles written by business school professors and industry leaders. Essential reading for executives and business professionals.",
        },
        {
            "title": "McKinsey & Company — Business Insights and Management Consulting",
            "url": "https://www.mckinsey.com/insights",
            "snippet": "McKinsey publishes free research reports on business strategy, technology adoption, digital transformation, and economic trends. Covers industry-specific insights across healthcare, finance, retail, and manufacturing. Cited by top executives worldwide.",
        },
        {
            "title": "Y Combinator — Startup Library and Funding for Founders",
            "url": "https://www.ycombinator.com",
            "snippet": "Y Combinator is the world's top startup accelerator. The YC library contains free essays, videos, and resources on building startups including fundraising, product-market fit, hiring, and growth. Funded Airbnb, Stripe, Dropbox, and more.",
        },
        {
            "title": "Gartner — Technology and Business Research and Advisory",
            "url": "https://www.gartner.com",
            "snippet": "Gartner provides authoritative technology and business research, market analysis, and advisory services. Known for the Magic Quadrant evaluating technology vendors. Trusted by CIOs, CEOs, and IT leaders for strategic decisions.",
        },
        {
            "title": "Forbes — Business News, Entrepreneurship and Innovation",
            "url": "https://www.forbes.com",
            "snippet": "Forbes covers business news, entrepreneurship, investing, and technology with a focus on wealth creation and innovation. Known for rankings like Forbes 500, billionaires list, and best companies to work for. Daily business news and analysis.",
        },
        {
            "title": "TechCrunch Startups — Startup Funding News and Venture Capital",
            "url": "https://techcrunch.com/startups",
            "snippet": "TechCrunch Startups covers funding rounds, acquisitions, IPOs, and startup launches. Tracks venture capital investments, Series A through IPO. Essential for founders, investors, and anyone following the startup ecosystem.",
        },
        {
            "title": "G2 — Business Software Reviews and Comparison Platform",
            "url": "https://www.g2.com",
            "snippet": "G2 is the world's largest software marketplace with 2 million verified user reviews. Compare business software across 2000+ categories including CRM, marketing, HR, and project management. Find the best tools for your business needs.",
        },
        {
            "title": "Product Hunt — Discover the Best New Products and Tools",
            "url": "https://www.producthunt.com",
            "snippet": "Product Hunt is the leading platform for discovering new products, apps, and tools. Upvote your favorites and read community reviews. Great for finding new AI tools, SaaS products, and developer tools before they go mainstream.",
        },
        {
            "title": "Statista — Market Research Data, Statistics and Industry Reports",
            "url": "https://www.statista.com",
            "snippet": "Statista aggregates market research data, statistics, and industry reports from 22,500+ sources. Covers market size, consumer behavior, industry trends, and company data across 170 industries in 150+ countries.",
        },
        {
            "title": "Wall Street Journal — Business and Financial News",
            "url": "https://www.wsj.com",
            "snippet": "The Wall Street Journal provides comprehensive business, financial, and economic news coverage. Known for in-depth investigative reporting on corporations, markets, and policy. Trusted by business professionals and investors worldwide.",
        },
    ],

    "general": [
        {
            "title": "Wikipedia — The Free Encyclopedia",
            "url": "https://www.wikipedia.org",
            "snippet": "Wikipedia is the world's largest free online encyclopedia with 60 million articles in 300+ languages. Written collaboratively by volunteers. Covers almost every topic imaginable with citations and links to primary sources.",
        },
        {
            "title": "Reddit — Communities, Discussions and Crowd-Sourced Knowledge",
            "url": "https://www.reddit.com",
            "snippet": "Reddit hosts communities (subreddits) covering every topic imaginable. Find honest reviews, expert advice, personal experiences, and discussions. Great for getting real-world opinions that aren't found in formal articles.",
        },
        {
            "title": "YouTube — Videos, Tutorials and Educational Content",
            "url": "https://www.youtube.com",
            "snippet": "YouTube is the world's largest video platform with educational channels covering every subject. Watch tutorials, lectures, documentary-style explanations, and how-to videos. Free to watch, with creator-supported content.",
        },
        {
            "title": "Medium — Articles, Essays and Expert Writing on Any Topic",
            "url": "https://medium.com",
            "snippet": "Medium publishes articles from independent writers and major publications. Covers technology, business, health, science, and culture. Mix of free and paywalled content. Known for thoughtful, in-depth essays.",
        },
        {
            "title": "Quora — Questions and Answers from Experts and Enthusiasts",
            "url": "https://www.quora.com",
            "snippet": "Quora is a Q&A platform where experts, professionals, and enthusiasts answer questions on every topic. Find opinions from doctors, lawyers, engineers, and specialists. Over 400 million monthly visitors.",
        },
        {
            "title": "Khan Academy — Free Education in Math, Science and More",
            "url": "https://www.khanacademy.org",
            "snippet": "Khan Academy offers free, world-class education for anyone, anywhere. Covers math, science, computing, economics, history, and test prep. Used by 130 million learners. Personalized learning paths with exercises and videos.",
        },
        {
            "title": "Coursera — Online Courses from Top Universities and Companies",
            "url": "https://www.coursera.org",
            "snippet": "Coursera offers online courses, professional certificates, and degrees from 300+ top universities and companies. Topics include data science, business, technology, and arts. Audit most courses for free or earn certificates.",
        },
        {
            "title": "WireHive — Best Tools and Resources Directory",
            "url": "https://www.wirecutter.com",
            "snippet": "Wirecutter (by The New York Times) tests and recommends the best products across every category. Rigorous, hands-on testing by expert journalists. Covers electronics, home goods, software, and services with unbiased reviews.",
        },
        {
            "title": "Lifehacker — Tips, Tricks and Productivity Guides",
            "url": "https://lifehacker.com",
            "snippet": "Lifehacker publishes practical tips, tricks, and guides for productivity, technology, finance, and everyday life. How-to articles, app recommendations, and life hacks. Covers both digital and real-world productivity topics.",
        },
        {
            "title": "Product Hunt — Find the Best New Products Every Day",
            "url": "https://www.producthunt.com",
            "snippet": "Product Hunt surfaces the best new products every day. Community upvotes decide the top products. Find new apps, tools, books, and tech products before they go mainstream. Great for discovering alternatives to existing tools.",
        },
    ],
}

# ── Topic Detection ────────────────────────────────────────────────────────────
TOPIC_SIGNALS = {
    "ai_tools": {
        "words": {"ai", "tool", "tools", "generate", "generation", "image", "picture", "art",
                  "gpt", "chatgpt", "midjourney", "dalle", "stable", "diffusion", "llm",
                  "chatbot", "free", "generator", "creative", "design", "photo", "video",
                  "illustration", "artwork", "draw", "drawing", "visual", "flux", "runway"},
        "phrases": ["ai tools", "free ai", "image generator", "ai art", "picture generation",
                    "ai image", "text to image", "generative ai", "ai generator", "best ai"],
    },
    "coding": {
        "words": {"python", "javascript", "java", "typescript", "code", "coding", "programming",
                  "api", "library", "framework", "tutorial", "debug", "error", "github",
                  "npm", "function", "class", "algorithm", "sql", "react", "node", "flask",
                  "django", "docker", "kubernetes", "git", "bash", "terminal", "compile"},
        "phrases": ["how to code", "programming tutorial", "python error", "javascript tutorial",
                    "how to build", "rest api", "machine learning code", "open source"],
    },
    "medical": {
        "words": {"symptom", "symptoms", "treatment", "disease", "health", "doctor", "medical",
                  "medicine", "therapy", "diagnosis", "patient", "hospital", "drug", "pain",
                  "fever", "headache", "infection", "cancer", "diabetes", "anxiety", "depression",
                  "medication", "vaccine", "virus", "chronic", "surgery", "clinic"},
        "phrases": ["symptoms of", "treatment for", "side effects", "how to treat", "is it normal",
                    "causes of", "home remedy", "medical advice"],
    },
    "research": {
        "words": {"research", "paper", "papers", "study", "survey", "arxiv", "academic", "journal",
                  "publication", "citation", "experiment", "hypothesis", "findings", "dataset",
                  "benchmark", "methodology", "peer", "reviewed", "literature", "thesis"},
        "phrases": ["research paper", "systematic review", "state of the art", "literature review",
                    "published paper", "academic paper", "scientific study", "peer reviewed"],
    },
    "news": {
        "words": {"news", "latest", "update", "updates", "breaking", "recent", "today",
                  "announced", "launched", "released", "this week", "current", "event",
                  "happened", "politics", "election", "war", "economy", "climate"},
        "phrases": ["latest news", "breaking news", "what happened", "recent update",
                    "just announced", "this year", "in 2025"],
    },
    "legal": {
        "words": {"law", "legal", "court", "regulation", "rights", "attorney", "contract",
                  "lawsuit", "legislation", "case", "judge", "lawyer", "act", "statute",
                  "compliance", "liability", "plaintiff", "defendant", "jurisdiction"},
        "phrases": ["is it legal", "legal advice", "court case", "my rights", "can i sue",
                    "legal guide", "under the law"],
    },
    "business": {
        "words": {"market", "startup", "revenue", "investment", "strategy", "business",
                  "entrepreneur", "funding", "roi", "profit", "saas", "b2b", "venture",
                  "capital", "growth", "sales", "marketing", "customer", "product", "launch"},
        "phrases": ["how to start a business", "startup funding", "business strategy",
                    "market analysis", "business plan", "go to market", "raise funding"],
    },
}


def _detect_topic(query: str) -> str:
    q = query.lower()
    words = set(q.split())
    scores = {}

    for topic, signals in TOPIC_SIGNALS.items():
        score = len(words & signals["words"])
        score += sum(2 for p in signals["phrases"] if p in q)
        scores[topic] = score

    best_score = max(scores.values())
    if best_score == 0:
        return "general"

    # Priority: ai_tools and coding are more specific, so they win ties
    for topic in ["ai_tools", "medical", "legal", "research", "news", "business", "coding"]:
        if scores[topic] == best_score:
            return topic

    return "general"


def get_demo_results(query: str, n: int = 10) -> list[dict]:
    """
    Return query-relevant demo results.
    Picks the right topic corpus based on query keywords,
    then mixes in a few off-topic results so re-ranking has something to reorder.
    """
    topic = _detect_topic(query)
    primary = list(TOPIC_CORPORA.get(topic, TOPIC_CORPORA["general"]))

    # Add 2-3 results from a secondary topic for re-ranking variety
    secondary_topic = "general" if topic != "general" else "coding"
    secondary = random.sample(TOPIC_CORPORA[secondary_topic], min(3, len(TOPIC_CORPORA[secondary_topic])))

    pool = primary + secondary
    random.shuffle(pool)

    # Deduplicate by URL
    seen = set()
    results = []
    for r in pool:
        if r["url"] not in seen:
            seen.add(r["url"])
            results.append(r)
        if len(results) >= n:
            break

    print(f"[Fetcher] Demo mode: topic={topic}, returning {len(results)} results")
    return results


# ── Live Search (DuckDuckGo) ───────────────────────────────────────────────────
def _parse_ddg_html(html: str, max_results: int = 10) -> list[dict]:
    results = []

    # Try primary pattern (DDG result blocks)
    blocks = re.findall(
        r'class="result__body".*?'
        r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'class="result__snippet"[^>]*>(.*?)</(?:a|span)>',
        html, re.DOTALL
    )

    for url, title, snippet in blocks[:max_results]:
        title   = re.sub(r'<[^>]+>', '', title).strip()
        snippet = re.sub(r'<[^>]+>', '', snippet).strip()
        url = url.strip()
        if title and url and url.startswith('http'):
            results.append({"title": title, "url": url, "snippet": snippet})

    if results:
        return results

    # Fallback pattern — broader match
    titles   = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
    snippets = re.findall(r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|span|div)>', html, re.DOTALL)

    for i, (url, title) in enumerate(titles[:max_results]):
        title   = re.sub(r'<[^>]+>', '', title).strip()
        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
        url = url.strip()
        if title and url and url.startswith('http'):
            results.append({"title": title, "url": url, "snippet": snippet})

    return results


def fetch_results(query: str, max_results: int = 10) -> list[dict]:
    """
    Live search via DuckDuckGo. Falls back to query-aware demo corpus on failure.
    """
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&kl=en-us&ia=web"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        results = _parse_ddg_html(resp.text, max_results)
        if results:
            print(f"[Fetcher] DDG returned {len(results)} results for: {query}")
            return results
        print("[Fetcher] DDG returned 0 parsed results, using demo corpus.")
    except Exception as e:
        print(f"[Fetcher] DDG failed ({e}), using demo corpus.")

    return get_demo_results(query, max_results)
