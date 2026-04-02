"""
Realistic sample data for Paper Trail Knowledge Graph.
Creates a well-connected network based on actual AI/ML research relationships.
"""

import asyncio
from app.services.neo4j_service import Neo4jService

async def populate_realistic_data():
    neo4j = Neo4jService()
    
    print("🔄 Creating constraints...")
    await neo4j.create_constraints()
    
    # ------------------------------------------------------------------
    # Authors (with realistic affiliations)
    # ------------------------------------------------------------------
    print("\n📝 Adding authors...")
    authors = [
        # Google Brain/DeepMind
        {"id": "ashish_vaswani", "name": "Ashish Vaswani", "affiliation": "Google Brain"},
        {"id": "sharan_narang", "name": "Sharan Narang", "affiliation": "Google Brain"},
        {"id": "parmar_niki", "name": "Niki Parmar", "affiliation": "Google Brain"},
        
        # OpenAI
        {"id": "tom_brown", "name": "Tom Brown", "affiliation": "OpenAI"},
        {"id": "alec_radford", "name": "Alec Radford", "affiliation": "OpenAI"},
        
        # Google AI / BERT Authors
        {"id": "jacob_devlin", "name": "Jacob Devlin", "affiliation": "Google AI"},
        {"id": "ming_wei_chang", "name": "Ming-Wei Chang", "affiliation": "Google AI"},
        
        # DeepMind / Vision
        {"id": "alexei_efros", "name": "Alexei Efros", "affiliation": "Meta AI / UC Berkeley"},
        {"id": "zhang_richard", "name": "Richard Zhang", "affiliation": "Meta AI"},
        
        # Stability AI / Diffusion
        {"id": "patrick_esser", "name": "Patrick Esser", "affiliation": "Stability AI"},
        {"id": "robin_rombach", "name": "Robin Rombach", "affiliation": "Stability AI"},
    ]
    
    for author in authors:
        await neo4j.upsert_author(author)
    print(f"  ✓ Added {len(authors)} authors")
    
    # ------------------------------------------------------------------
    # Papers (realistic AI/ML papers)
    # ------------------------------------------------------------------
    print("\n📚 Adding papers...")
    papers = [
        # Foundation models
        {
            "id": "transformer_2017",
            "title": "Attention Is All You Need",
            "abstract": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
            "published_date": "2017-06-12",
            "url": "https://arxiv.org/abs/1706.03762",
            "doi": "10.48550/arXiv.1706.03762",
            "source": "arXiv",
            "embedding": None
        },
        {
            "id": "bert_2018",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "abstract": "We introduce BERT, a method for pre-training general-purpose language representations by jointly conditioning on both left and right context in all layers.",
            "published_date": "2018-10-11",
            "url": "https://arxiv.org/abs/1810.04805",
            "doi": "10.48550/arXiv.1810.04805",
            "source": "arXiv",
            "embedding": None
        },
        {
            "id": "gpt3_2020",
            "title": "Language Models are Few-Shot Learners",
            "abstract": "Recent work has demonstrated substantial gains on many NLP tasks by scaling up language models as a path to improved performance. We study the few-shot learning abilities of large language models.",
            "published_date": "2020-05-28",
            "url": "https://arxiv.org/abs/2005.14165",
            "doi": "10.48550/arXiv.2005.14165",
            "source": "arXiv",
            "embedding": None
        },
        
        # Vision models
        {
            "id": "vit_2020",
            "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
            "abstract": "While the Transformer architecture has become the de-facto standard for natural language processing, its applications to computer vision remain limited. We show that a pure transformer applied directly to sequences of image patches can perform very well on image classification tasks.",
            "published_date": "2020-10-22",
            "url": "https://arxiv.org/abs/2010.11929",
            "doi": "10.48550/arXiv.2010.11929",
            "source": "arXiv",
            "embedding": None
        },
        {
            "id": "clip_2021",
            "title": "Learning Transferable Visual Models From Natural Language Supervision",
            "abstract": "State-of-the-art computer vision systems are trained to predict a fixed set of object categories, limiting their generality and usability. We demonstrate that the simple pre-training task of predicting which caption goes with which image is an efficient and scalable way to learn SOTA image representations from scratch on a dataset of 400 million (image, text) pairs collected from the internet.",
            "published_date": "2021-02-26",
            "url": "https://arxiv.org/abs/2103.14030",
            "doi": "10.48550/arXiv.2103.14030",
            "source": "arXiv",
            "embedding": None
        },
        
        # Generative models
        {
            "id": "diffusion_2020",
            "title": "Denoising Diffusion Probabilistic Models",
            "abstract": "We present high quality image synthesis results using diffusion probabilistic models, a class of latent variable models inspired by considerations from nonequilibrium thermodynamics. By closely coupling the design of the network architecture and the diffusion process, we achieve state-of-the-art inpainting results on multiple datasets.",
            "published_date": "2020-12-16",
            "url": "https://arxiv.org/abs/2006.11239",
            "doi": "10.48550/arXiv.2006.11239",
            "source": "arXiv",
            "embedding": None
        },
        {
            "id": "stable_diffusion_2022",
            "title": "High-Resolution Image Synthesis with Latent Diffusion Models",
            "abstract": "By decomposing the image formation process into a sequential application of the diffusion process combined with spatial compression, we obtain a fast, efficient and effective inductive bias for learning complex data distributions. We demonstrate that this approach dramatically improves upon previous diffusion-based text-to-image synthesis methods and compares favorably to other state-of-the-art approaches across a variety of tasks.",
            "published_date": "2022-04-13",
            "url": "https://arxiv.org/abs/2112.10752",
            "doi": "10.48550/arXiv.2112.10752",
            "source": "arXiv",
            "embedding": None
        },
        
        # Reasoning and planning
        {
            "id": "chain_of_thought_2022",
            "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
            "abstract": "We explore how generating a chain of thought—a series of intermediate reasoning steps—significantly improves the ability of large language models to perform complex reasoning. We observe benefits across arithmetic, commonsense, and symbolic reasoning tasks.",
            "published_date": "2022-01-28",
            "url": "https://arxiv.org/abs/2201.11903",
            "doi": "10.48550/arXiv.2201.11903",
            "source": "arXiv",
            "embedding": None
        },
    ]
    
    for paper in papers:
        await neo4j.upsert_paper(paper)
    print(f"  ✓ Added {len(papers)} papers")
    
    # ------------------------------------------------------------------
    # Author-Paper relationships (realistic authorship)
    # ------------------------------------------------------------------
    print("\n🔗 Linking authors to papers...")
    authorship = [
        ("ashish_vaswani", "transformer_2017"),
        ("sharan_narang", "transformer_2017"),
        ("parmar_niki", "transformer_2017"),
        
        ("jacob_devlin", "bert_2018"),
        ("ming_wei_chang", "bert_2018"),
        
        ("tom_brown", "gpt3_2020"),
        ("alec_radford", "gpt3_2020"),
        
        ("alexei_efros", "vit_2020"),
        ("alec_radford", "clip_2021"),
        ("zhang_richard", "clip_2021"),
        
        ("robin_rombach", "diffusion_2020"),
        ("robin_rombach", "stable_diffusion_2022"),
        ("patrick_esser", "stable_diffusion_2022"),
        
        ("tom_brown", "chain_of_thought_2022"),
    ]
    
    for author_id, paper_id in authorship:
        await neo4j.link_author_paper(author_id, paper_id)
    print(f"  ✓ Created {len(authorship)} authorship relationships")
    
    # ------------------------------------------------------------------
    # Paper citations (realistic dependency)
    # ------------------------------------------------------------------
    print("\n📖 Adding paper citations...")
    citations = [
        # BERT cites Transformer
        ("bert_2018", "transformer_2017"),
        # GPT-3 uses Transformer principles
        ("gpt3_2020", "transformer_2017"),
        # ViT uses Transformer
        ("vit_2020", "transformer_2017"),
        # CLIP builds on ViT
        ("clip_2021", "vit_2020"),
        # Stable Diffusion improves on Diffusion
        ("stable_diffusion_2022", "diffusion_2020"),
        # Chain-of-thought uses LLMs like GPT-3
        ("chain_of_thought_2022", "gpt3_2020"),
    ]
    
    for citing_id, cited_id in citations:
        await neo4j.link_citation(citing_id, cited_id)
    print(f"  ✓ Created {len(citations)} citation relationships")
    
    # ------------------------------------------------------------------
    # Concepts (research topics)
    # ------------------------------------------------------------------
    print("\n💡 Adding concepts...")
    concepts = [
        {"id": "attention", "name": "Attention Mechanism", "description": "Neural network mechanism to focus on relevant information", "embedding": None},
        {"id": "transformer", "name": "Transformer Architecture", "description": "Deep learning architecture using self-attention", "embedding": None},
        {"id": "pretraining", "name": "Pre-training", "description": "Training on large unlabeled datasets", "embedding": None},
        {"id": "language_model", "name": "Language Model", "description": "Model trained to predict text sequences", "embedding": None},
        {"id": "vision", "name": "Computer Vision", "description": "AI for analyzing images and video", "embedding": None},
        {"id": "multimodal", "name": "Multimodal Learning", "description": "Learning from multiple input types", "embedding": None},
        {"id": "generative", "name": "Generative Model", "description": "Model that generates new samples", "embedding": None},
        {"id": "diffusion", "name": "Diffusion Model", "description": "Generative model using diffusion process", "embedding": None},
        {"id": "reasoning", "name": "Reasoning", "description": "Complex multi-step problem solving", "embedding": None},
    ]
    
    for concept in concepts:
        await neo4j.upsert_concept(concept)
    print(f"  ✓ Added {len(concepts)} concepts")
    
    # ------------------------------------------------------------------
    # Paper-Concept relationships
    # ------------------------------------------------------------------
    print("\n🔗 Linking papers to concepts...")
    paper_concepts = [
        # Transformer
        ("transformer_2017", "attention"),
        ("transformer_2017", "transformer"),
        
        # BERT
        ("bert_2018", "transformer"),
        ("bert_2018", "pretraining"),
        ("bert_2018", "language_model"),
        
        # GPT-3
        ("gpt3_2020", "language_model"),
        ("gpt3_2020", "pretraining"),
        ("gpt3_2020", "reasoning"),
        
        # ViT
        ("vit_2020", "transformer"),
        ("vit_2020", "vision"),
        
        # CLIP
        ("clip_2021", "vision"),
        ("clip_2021", "multimodal"),
        ("clip_2021", "pretraining"),
        
        # Diffusion
        ("diffusion_2020", "generative"),
        ("diffusion_2020", "diffusion"),
        
        # Stable Diffusion
        ("stable_diffusion_2022", "generative"),
        ("stable_diffusion_2022", "diffusion"),
        ("stable_diffusion_2022", "multimodal"),
        
        # Chain-of-thought
        ("chain_of_thought_2022", "reasoning"),
        ("chain_of_thought_2022", "language_model"),
    ]
    
    for paper_id, concept_id in paper_concepts:
        await neo4j.link_paper_concept(paper_id, concept_id)
    print(f"  ✓ Created {len(paper_concepts)} paper-concept relationships")
    
    # ------------------------------------------------------------------
    # Concept-Concept relationships
    # ------------------------------------------------------------------
    print("\n🔗 Linking concepts...")
    concept_links = [
        ("attention", "transformer"),
        ("transformer", "language_model"),
        ("transformer", "vision"),
        ("pretraining", "language_model"),
        ("language_model", "reasoning"),
        ("vision", "multimodal"),
        ("language_model", "multimodal"),
        ("generative", "diffusion"),
        ("diffusion", "multimodal"),
    ]
    
    for concept_a, concept_b in concept_links:
        await neo4j.link_concepts(concept_a, concept_b)
    print(f"  ✓ Created {len(concept_links)} concept-concept relationships")
    
    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    await neo4j.close()
    print("\n" + "="*60)
    print("✅ Realistic graph population complete!")
    print("="*60)
    print(f"  👥 Authors: {len(authors)}")
    print(f"  📚 Papers: {len(papers)}")
    print(f"  💡 Concepts: {len(concepts)}")
    print(f"  📝 Authorship: {len(authorship)}")
    print(f"  📖 Citations: {len(citations)}")
    print(f"  🔗 Paper-Concept: {len(paper_concepts)}")
    print(f"  💭 Concept-Concept: {len(concept_links)}")
    total_relationships = len(authorship) + len(citations) + len(paper_concepts) + len(concept_links)
    print(f"  📊 Total Relationships: {total_relationships}")
    print("\n🌐 View at: http://localhost:3000")

if __name__ == "__main__":
    asyncio.run(populate_realistic_data())
