#!/usr/bin/env python3
import requests
import json

def test_api():
    # Base URL
    base_url = 'http://localhost:8000/api'
    
    # Test 1: Add test papers
    print("Adding test papers...")
    response = requests.post(f"{base_url}/dev/add-test-papers")
    print(f"Response: {response.status_code}")
    print(response.json())
    
    # Test 2: Add a real paper (manually)
    print("\nAdding a real paper...")
    real_paper = {
        'id': '732ce53c573475f2691a7cfc716cf4f568d17360',
        'title': 'How Johnny Can Persuade LLMs to Jailbreak Them: Rethinking Persuasion to Challenge AI Safety by Humanizing LLMs',
        'authors': [
            'Yi Zeng',
            'Hongpeng Lin',
            'Jingwen Zhang',
            'Diyi Yang',
            'Ruoxi Jia',
            'Weiyan Shi'
        ],
        'abstract': 'Most traditional AI safety research has approached AI models as machines and centered on algorithm-focused attacks developed by security experts. As large language models (LLMs) become increasingly common and competent, non-expert users can also impose risks during daily interactions. This paper introduces a new perspective to jailbreak LLMs as human-like communicators, to explore this overlooked intersection between everyday language interaction and AI safety. Specifically, we study how to persuade LLMs to jailbreak them. First, we propose a persuasion taxonomy derived from decades of social science research. Then, we apply the taxonomy to automatically generate interpretable persuasive adversarial prompts (PAP) to jailbreak LLMs. Results show that persuasion significantly increases the jailbreak performance across all risk categories: PAP consistently achieves an attack success rate of over 92% on Llama 2-7b Chat, GPT-3.5, and GPT-4 in 10 trials, surpassing recent algorithm-focused attacks. On the defense side, we explore various mechanisms against PAP and, found a significant gap in existing defenses, and advocate for more fundamental mitigation for highly interactive LLMs',
        'url': 'https://arxiv.org/pdf/2401.06373.pdf',
        'venue': 'Annual Meeting of the Association for Computational Linguistics',
        'submitted_date': '2024-01-12',
        'tldr': 'This paper proposes a persuasion taxonomy derived from decades of social science research and applies the taxonomy to automatically generate interpretable persuasive adversarial prompts (PAP) to jailbreak LLMs.',
        'highlight': True,
        'tags': ['ai-safety', 'jailbreak', 'persuasion'],
        'posted': True,
        'include_on_website': True
    }
    
    # Add directly to the mock database through the dev endpoint
    response = requests.post(f"{base_url}/dev/add-custom-paper", json=real_paper)
    if response.status_code == 200:
        print("Real paper added successfully")
    else:
        print(f"Failed to add real paper: {response.status_code}")
    
    # Test 3: Get papers
    print("\nGetting papers...")
    response = requests.get(f"{base_url}/papers")
    print(f"Response: {response.status_code}")
    papers = response.json()
    print(f"Found {len(papers)} papers")
    for i, paper in enumerate(papers):
        print(f"{i+1}. {paper['title']} (ID: {paper['uid']})")
    
    # Test 4: Get highlighted papers
    print("\nGetting highlighted papers...")
    response = requests.get(f"{base_url}/papers/highlighted")
    print(f"Response: {response.status_code}")
    highlighted = response.json()
    print(f"Found {len(highlighted)} highlighted papers")
    if highlighted:
        print(f"First highlighted paper: {highlighted[0]['title']}")
    
    # Test 5: Get paper details
    if papers:
        paper_id = papers[0]['uid']
        print(f"\nGetting details for paper {paper_id}...")
        response = requests.get(f"{base_url}/papers/{paper_id}")
        print(f"Response: {response.status_code}")
        details = response.json()
        print(f"Paper details: {details['title']}")

if __name__ == "__main__":
    test_api()