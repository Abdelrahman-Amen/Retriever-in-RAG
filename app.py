import streamlit as st  # For building the app interface
from langchain_community.document_loaders import PyPDFLoader  # To load PDF files
from langchain.text_splitter import RecursiveCharacterTextSplitter  # To split text into chunks
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI  # For embeddings and generative AI
from langchain_community.vectorstores import FAISS  # For vector database and similarity search
from langchain.chains.combine_documents import create_stuff_documents_chain  # To chain document chunks
from langchain.chains import create_retrieval_chain  # For creating RAG pipelines
from langchain_core.prompts import ChatPromptTemplate  # To structure prompts for generative AI
from dotenv import load_dotenv  # To load environment variables
import os  # For environment variable management

# Load environment variables (e.g., API key)
load_dotenv()

# Streamlit UI
st.title("PDF Question Answering App")  # App title
st.write("Upload a PDF and ask a question based on its content.")  # App description

# File uploader for PDFs
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    # Save the uploaded file locally for processing
    with open("uploaded_file.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Load and process the PDF file
    loader = PyPDFLoader("uploaded_file.pdf")  # Read PDF content
    docs = loader.load()  # Extract document content

    # Split the document into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    documents = text_splitter.split_documents(docs)

    # Create a FAISS vector database using embeddings
    db = FAISS.from_documents(documents, GoogleGenerativeAIEmbeddings(model="models/embedding-001"))

    # Initialize the generative AI model for answering questions
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=os.getenv("GOOGLE_API_KEY"))

    # Define a prompt template to structure input for the model
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context with clarification. 
    <context>
    {context}
    </context>
    Question: {input}
    """)

    # Combine the document retriever and the generative model
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Create the retriever to fetch relevant document chunks
    retriever = db.as_retriever()

    # Combine retriever and document chain for retrieval-augmented generation
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    # User input for the question
    question = st.text_input("Enter your question:")

    if question:
        try:
            # Generate an answer using the retrieval chain
            response = retrieval_chain.invoke({"input": question})
            answer = response.get("answer", "No answer returned.")
            st.subheader("Answer:")  # Display the answer
            st.write(answer)
        except Exception as e:
            st.error(f"Error during chain invocation: {e}")  # Handle errors gracefully
