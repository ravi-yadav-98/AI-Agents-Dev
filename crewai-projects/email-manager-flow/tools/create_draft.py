from langchain.tools import tool
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.create_draft import GmailCreateDraft

# --- Improvement 1: Initialize the toolkit and tool only once ---
# This avoids re-authenticating or re-creating objects on every call.
gmail_toolkit = GmailToolkit()
# gmail_create_draft_tool = GmailCreateDraft(api_resource=gmail_toolkit.api_resource)
gmail_toolkit.get_tools()

# @tool("Create Draft")
# def create_draft(data: str) -> str:
#     """
#     Useful to create an email draft.
#     The input to this tool should be a pipe (|) separated text
#     of length 3 (three), representing who to send the email to,
#     the subject of the email and the actual message.
#     For example, `lorem@ipsum.com|Nice To Meet You|Hey it was great to meet you.`.
#     """
#     # --- Improvement 2: Add error handling for bad input ---
#     try:
#         email, subject, message = data.split("|")
#         # Call the pre-initialized tool's run method
#         result = gmail_create_draft_tool.run(
#             {"to": [email], "subject": subject, "message": message}
#         )
#         return f"\nDraft created successfully. Result: {result}\n"
#     except ValueError:
#         return "Error: Input is not formatted correctly. Please provide input as 'to|subject|message'."
#     except Exception as e:
#         return f"An unexpected error occurred: {e}"

# # To use this tool, you would import `create_draft` and add it to your agent's tool list.