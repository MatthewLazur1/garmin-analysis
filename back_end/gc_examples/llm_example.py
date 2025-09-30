import streamlit as st
import google.generativeai as genai
import chromadb
import textwrap
from io import BytesIO
from PyPDF2 import PdfReader

# --- Helper Functions ---

def get_pdf_text(pdf_doc):
    """Extracts text from a PDF document."""
    text = ""
    pdf_reader = PdfReader(BytesIO(pdf_doc.read()))
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def split_text_into_chunks(text, chunk_size=1000, chunk_overlap=200):
    """Splits text into overlapping chunks."""
    chunks = []
    start_index = 0
    while start_index < len(text):
        end_index = start_index + chunk_size
        chunks.append(text[start_index:end_index])
        start_index += chunk_size - chunk_overlap
    return chunks

# --- Main Application ---

# Set up the Streamlit page
st.set_page_config(page_title="Chat With Your Documents", layout="wide")
st.title("📄 Chat With Your Documents (using Gemini & ChromaDB)")
st.write("This app allows you to chat with your own PDF documents using Google's Gemini Pro and the ChromaDB vector store. All for free!")

# --- 1. API Key and Model Configuration ---
with st.sidebar:
    st.header("Configuration")
    google_api_key = st.text_input("Enter your Google API Key:", type="password")

    if google_api_key:
        try:
            genai.configure(api_key=google_api_key)
            st.success("API Key configured successfully!")
        except Exception as e:
            st.error(f"Error configuring API key: {e}")
            st.stop()
    else:
        st.info("Please enter your Google API Key to proceed.")
        st.stop()

# Initialize the generative and embedding models
try:
    llm = genai.GenerativeModel('gemini-pro')
    embedding_model = 'models/embedding-001'
except Exception as e:
    st.error(f"Error initializing Google models: {e}")
    st.info("Please ensure your API key is correct and has access to the Gemini API.")
    st.stop()

# --- 2. File Upload and Processing ---
st.header("1. Upload Your PDF")
uploaded_file = st.file_uploader("Upload a PDF file and I'll help you query it.", type="pdf")

if uploaded_file:
    # --- 3. Vector Store and RAG Pipeline ---
    with st.spinner("Processing PDF... This may take a moment."):
        # Extract text from PDF
        document_text = get_pdf_text(uploaded_file)

        # Split text into chunks
        text_chunks = split_text_into_chunks(document_text)

        # Initialize ChromaDB client and create a collection
        # Using a simple in-memory ChromaDB instance
        client = chromadb.Client()
        # You can use .PersistentClient(path="/path/to/db") to save to disk
        collection_name = f"doc_{uploaded_file.name}"
        if collection_name in [c.name for c in client.list_collections()]:
             client.delete_collection(name=collection_name)
        collection = client.create_collection(name=collection_name)


        # Generate embeddings and store in ChromaDB
        st.write("Generating embeddings and building vector store...")
        doc_ids = [str(i) for i in range(len(text_chunks))]
        
        # Note: The free Gemini API has a rate limit.
        # For large documents, you might need to add a delay between API calls.
        embeddings = genai.embed_content(model=embedding_model,
                                         content=text_chunks,
                                         task_type="retrieval_document")
                                         
        collection.add(
            embeddings=embeddings['embedding'],
            documents=text_chunks,
            ids=doc_ids
        )
        st.success(f"PDF processed successfully! The vector store contains {len(text_chunks)} text chunks.")
        st.session_state.collection = collection # Store collection in session state
        st.session_state.file_processed = True


# --- 4. User Query and Response ---
if 'file_processed' in st.session_state and st.session_state.file_processed:
    st.header("2. Ask Questions About Your Document")
    user_question = st.text_input("What would you like to know?")

    if user_question:
        with st.spinner("Searching for answers..."):
            # 1. Generate embedding for the user's question
            question_embedding = genai.embed_content(model=embedding_model,
                                                     content=user_question,
                                                     task_type="retrieval_query")['embedding']

            # 2. Query ChromaDB to find relevant chunks
            results = st.session_state.collection.query(
                query_embeddings=[question_embedding],
                n_results=5 # Get the top 5 most relevant chunks
            )
            retrieved_chunks = results['documents'][0]

            # 3. Construct the prompt for the LLM
            context = "\n\n".join(retrieved_chunks)
            prompt = textwrap.dedent(f"""
            Answer the following question based on the provided context.
            If the answer is not in the context, say "I couldn't find the answer in the document."

            CONTEXT:
            {context}

            QUESTION:
            {user_question}

            ANSWER:
            """)

            # 4. Generate the response
            try:
                response = llm.generate_content(prompt)
                st.markdown("### Answer:")
                st.markdown(response.text)

                with st.expander("Show Retrieved Context"):
                    st.write(context)
            except Exception as e:
                st.error(f"An error occurred while generating the answer: {e}")