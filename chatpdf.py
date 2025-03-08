#2
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") 
genai.configure(api_key=api_key)  


## Function to extract text from uploaded PDFs
def get_pdf_text(pdf_docs):
    text = "" 
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)  
        for page in pdf_reader.pages:
            page_text = page.extract_text() or ""  
            text += page_text 
    return text


## Function to split extracted text into smaller chunks for processing
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text) 
    return chunks


## Function to create a FAISS vector store for similarity search
def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)  
    vector_store.save_local("faiss_index") 


## Function to initialize conversation chain using Gemini AI
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context. Make sure to provide all details.
    If the answer is not in the provided context, just say, "Answer is not available in the context."
    Do not provide incorrect information.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.3) 

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)  # Load QA chain

    return chain


## Function to process user question and retrieve answer
def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question) 
    chain = get_conversational_chain()  

    # Generate response using the correct key "input_documents"
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)

    print(response)  # Debugging: Print response in console
    st.write("Reply:", response["output_text"])  # Display response in Streamlit




## Streamlit app main function
def main():
    st.set_page_config(page_title="Chat PDF")  # Set page title
    st.header("Chat with PDF using Gemini💁")  # Set page header

    # User input for asking questions
    user_question = st.text_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question)  # Process user input

    # Sidebar for uploading PDFs
    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your PDF Files", accept_multiple_files=True)

        # Process PDFs only if files are uploaded
        if pdf_docs and st.button("Submit & Process"):
            with st.spinner("Processing..."): 
                raw_text = get_pdf_text(pdf_docs) 
                text_chunks = get_text_chunks(raw_text) 
                get_vector_store(text_chunks)
                st.success("Processing Complete ✅")  


## Run the Streamlit app
if __name__ == "__main__":
    main()
