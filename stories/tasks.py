from openai import OpenAI
from .models import Paragraph, Chapter
import requests
import os
import json

# Initialize OpenAI client - it will automatically use OPENAI_API_KEY from environment
client = OpenAI()

def generate_next_paragraph(chapter_id, previous_paragraph_id=None):
    """
    Generate the next paragraph using OpenAI's chat API based on the previous paragraph.
    """
    try:
        chapter = Chapter.objects.get(id=chapter_id)
        
        # Get context and current page from previous paragraph if it exists
        context = ""
        current_page = 1
        if previous_paragraph_id:
            previous_paragraph = Paragraph.objects.get(id=previous_paragraph_id)
            context = previous_paragraph.text
            current_page = previous_paragraph.page

        # Get the next paragraph number for the current page
        next_paragraph_number = Paragraph.objects.filter(
            chapter=chapter,
            page=current_page
        ).count() + 1

        # Create the prompt
        system_prompt = "You are a creative writer continuing a story. Write the next paragraph naturally continuing from the previous text."
        user_message = f"Previous paragraph: {context}\n\nWrite the next paragraph:"

        # Generate the response
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        print(f"Generated paragraph: {response.choices[0].message.content}")

        # Create and save the new paragraph with correct numbering
        new_paragraph = Paragraph.objects.create(
            chapter=chapter,
            text=response.choices[0].message.content,
            paragraph_number=next_paragraph_number,
            page=current_page,
            is_locked=False
        )

        return new_paragraph

    except Exception as e:
        print(f"Error generating paragraph: {e}")
        raise

def analyze_and_add_links(paragraph_id):
    """
    Analyze an existing paragraph for potential wiki-style links and update its HTML version.
    """
    try:
        paragraph = Paragraph.objects.get(id=paragraph_id)
        
        # Identify potential link phrases
        system_prompt = """You are an AI that identifies important words or phrases that could be wiki-style links.
        Select 2-4 significant nouns or phrases that could lead to interesting related content.
        Return the paragraph with the links added in HTML format. Only return the paragraph text, not the prompt, quotes, or anything else."""
        
        user_message = f"Identify potential link phrases in this text:\n\n{paragraph.text}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
        )

        links_data = response.choices[0].message.content

        # Update the paragraph
        paragraph.text_with_links = links_data
        paragraph.save()

        print(f"Links added to paragraph {paragraph.id}: {links_data}")

        return links_data

    except Exception as e:
        print(f"Error analyzing paragraph for links: {e}")
        raise

def generate_next_page(chapter_id, current_page):
    """
    Generate the first paragraph of a new page using OpenAI's chat API based on the chapter's context.
    """
    try:
        chapter = Chapter.objects.get(id=chapter_id)
        
        # Get all paragraphs from the current chapter up to the current page
        previous_paragraphs = Paragraph.objects.filter(
            chapter=chapter,
            page__lte=current_page
        ).order_by('page', 'paragraph_number')
        
        # Combine the text of previous paragraphs
        context = "\n".join([p.text for p in previous_paragraphs])

        # Create the prompt
        system_prompt = """You are a creative writer continuing a story. Based on the previous content of this chapter, 
        write the first paragraph of the next page. Ensure it flows naturally from the previous content while advancing 
        the story."""
        
        user_message = f"Previous content of the chapter:\n\n{context}\n\nWrite the first paragraph of the next page:"

        # Generate the response
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )

        # Create and save the new paragraph
        new_paragraph = Paragraph.objects.create(
            chapter=chapter,
            text=response.choices[0].message.content,
            paragraph_number=1,  # First paragraph of the new page
            page=current_page + 1,
            is_locked=False
        )

        return new_paragraph

    except Exception as e:
        print(f"Error generating next page: {e}")
        raise

# Get environment variables
signer_public_key = os.environ.get('SIGNER_PUBLIC_KEY')
crossmint_api_key = os.environ.get('CROSSMINT_API_KEY')

def create_wallet(signer_public_key=signer_public_key, api_key=crossmint_api_key):
    response = requests.post(
        "https://staging.crossmint.com/api/v1-alpha2/wallets",
        headers={
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        },
        json={
            "type": "evm-smart-wallet",
            "config": {
                "signer": {
                    "type": "evm-keypair",
                    "address": signer_public_key
                }
            }
        }
    )
    return response.json()

def create_nft(api_key=crossmint_api_key, collection_id=None, chain="solana", env="staging"):
    if not collection_id:
        collection_response = create_collection(api_key=api_key, chain=chain, env=env)
        print(f"Collection created: {collection_response}")
        collection_id = collection_response['id']
    
    # Using a valid Solana address format
    recipient_address = "solana:5FHwkrdxkN8yPBkLZM1X3jKHgvzxM3T6oF8VyuxWSjAM"
    url = f"https://{env}.crossmint.com/api/2022-06-09/collections/{collection_id}/nfts"
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    body = {
        "metadata": {
            "name": "Crossmint Example NFT",
            "image": "https://www.crossmint.com/assets/crossmint/logo.png",
            "description": "My NFT created via the mint API!"
        },
        "recipient": recipient_address,
        "sendNotification": True,
        "locale": "en-US",
        "reuploadLinkedFiles": True,
        "compressed": True  # Including this since we're using Solana
    }
    
    try:
        print(f"Sending request to: {url}")
        print(f"Request body: {body}")
        response = requests.post(url, headers=headers, json=body)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error minting NFT: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        raise

def create_collection(api_key=crossmint_api_key, chain="solana", env="staging"):
    url = f"https://{env}.crossmint.com/api/2022-06-09/collections/"

    payload = {
        "chain": chain,
        "metadata": {
            "name": "Sample NFT Collection",
            "imageUrl": "https://www.crossmint.com/assets/crossmint/logo.png",
            "description": "This is a sample NFT collection"
        },
        "fungibility": "non-fungible",
        "transferable": True,
        "supplyLimit": 123,
        "reuploadLinkedFiles": True
    }

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating collection: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        raise
