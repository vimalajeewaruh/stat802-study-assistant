import hmac

import streamlit as st
from anthropic import Anthropic


# ---------------------------------------------------------
# 1. Configure the Streamlit page
# ---------------------------------------------------------

st.set_page_config(
    page_title="Statistics Study Assistant",
    page_icon="📊",
    layout="centered",
)


# ---------------------------------------------------------
# 2. Require the shared course password
# ---------------------------------------------------------

def require_course_password():

    # If access was already granted during this browser session,
    # continue directly to the application.
    if st.session_state.get("course_access", False):
        return

    st.title("📊 Statistics Study Assistant")

    st.write(
        "Enter the STAT 802 course password to access the "
        "study assistant."
    )

    correct_password = str(
        st.secrets.get("APP_PASSWORD", "")
    )

    if not correct_password:
        st.error(
            "The course password has not been configured. "
            "Please contact the instructor."
        )
        st.stop()

    entered_password = st.text_input(
        "Course password",
        type="password",
        placeholder="Enter the course password",
    )

    if st.button(
        "Enter the application",
        type="primary",
    ):

        if hmac.compare_digest(
            entered_password,
            correct_password,
        ):
            st.session_state["course_access"] = True
            st.session_state["request_count"] = 0
            st.rerun()

        else:
            st.error("The course password is incorrect.")

    st.stop()


# Require password before continuing
require_course_password()


# ---------------------------------------------------------
# 3. Read configuration and create Anthropic client
# ---------------------------------------------------------

api_key = str(
    st.secrets.get("ANTHROPIC_API_KEY", "")
)

if not api_key:
    st.error(
        "The Anthropic API key has not been configured. "
        "Please contact the instructor."
    )
    st.stop()


client = Anthropic(
    api_key=api_key
)


# Maximum number of requests in one browser session
MAX_REQUESTS_PER_SESSION = int(
    st.secrets.get(
        "MAX_REQUESTS_PER_SESSION",
        20,
    )
)


if "request_count" not in st.session_state:
    st.session_state["request_count"] = 0


# ---------------------------------------------------------
# 4. Sidebar
# ---------------------------------------------------------

st.sidebar.header("STAT 802")

st.sidebar.write(
    "Statistics Study Assistant"
)

st.sidebar.write(
    "Requests during this session: "
    f"{st.session_state['request_count']} / "
    f"{MAX_REQUESTS_PER_SESSION}"
)


if st.sidebar.button("End study session"):

    st.session_state["course_access"] = False
    st.session_state["request_count"] = 0

    st.rerun()


# ---------------------------------------------------------
# 5. Main application interface
# ---------------------------------------------------------

st.title("📊 Statistics Study Assistant")

st.write(
    "Ask a statistics question to receive a clear explanation "
    "with examples relevant to applied sciences."
)

question = st.text_area(
    "Enter your statistics question:",
    height=160,
    placeholder=(
        "For example: Explain the difference between fixed and "
        "random treatment effects."
    ),
)


# ---------------------------------------------------------
# 6. Submit the question to Claude
# ---------------------------------------------------------

if st.button(
    "Ask Claude",
    type="primary",
):

    if not question.strip():

        st.warning("Please enter a question.")

    elif len(question) > 5000:

        st.warning(
            "Please limit your question to 5,000 characters."
        )

    elif (
        st.session_state["request_count"]
        >= MAX_REQUESTS_PER_SESSION
    ):

        st.error(
            "You have reached the request limit for this study "
            "session. Select 'End study session' and contact the "
            "instructor if you need additional access."
        )

    else:

        with st.spinner(
            "Preparing the explanation..."
        ):

            try:

                response = client.messages.create(
                    model="claude-haiku-5-5",
                    max_tokens=1200,
                    system=(
                        "You are a statistics teaching assistant "
                        "for STAT 802. "

                        "Help students understand statistical concepts "
                        "using clear explanations, mathematical accuracy, "
                        "and relevant examples. "

                        "When appropriate, use applications from "
                        "agriculture, animal science, horticulture, "
                        "food science, and environmental science. "

                        "Organize longer responses using short headings, "
                        "paragraphs, bullet points, and mathematical "
                        "notation when helpful. "

                        "Encourage learning rather than simply completing "
                        "graded assignments. "

                        "Do not claim that simulated examples are real "
                        "experimental data. Never invent references, "
                        "datasets, or research results."
                    ),
                    messages=[
                        {
                            "role": "user",
                            "content": question,
                        }
                    ],
                )

                answer = "\n".join(
                    block.text
                    for block in response.content
                    if block.type == "text"
                )

                if answer:

                    st.session_state["request_count"] += 1

                    st.markdown("### Explanation")
                    st.markdown(answer)

                    st.caption(
                        f"Input tokens: "
                        f"{response.usage.input_tokens} | "
                        f"Output tokens: "
                        f"{response.usage.output_tokens}"
                    )

                else:

                    st.warning(
                        "Claude returned a response, but it did "
                        "not contain a text explanation."
                    )

            except Exception as error:

                st.error(
                    f"The request could not be completed: {error}"
                )


# ---------------------------------------------------------
# 7. Privacy reminder
# ---------------------------------------------------------

st.divider()

st.caption(
    "This application is intended for ungraded learning and review. "
    "Do not enter grades, student identification numbers, medical "
    "information, research-participant information, or other "
    "sensitive personal information."
)