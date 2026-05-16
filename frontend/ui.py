import os
import time

import requests
import streamlit as st
from css import css_mkdown
from dotenv import load_dotenv

load_dotenv()
APP_PASSWORD = os.getenv("APP_PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")


def stream_response(query, chat_history):
    payload = {"query": query, "history": chat_history}
    response = requests.post(f"http://{HOST}:{PORT}/query/", json=payload)
    response.raise_for_status()

    data = response.json()
    answer = str(data.get("answer", ""))

    documents = data.get("documents", [])

    # Потоковый вывод текста по символам
    for char in answer:
        yield char, None
        time.sleep(0.001)

    yield None, documents


def setup_sidebar():
    st.sidebar.title("Параметры")
    if "sidebar_options" not in st.session_state:
        st.session_state.sidebar_options = {}


def main_app():
    st.set_page_config(page_title="Проводник", layout="centered")
    st.title("AgroGAU")

    # CSS
    st.markdown(css_mkdown, unsafe_allow_html=True)

    # Инициализация истории
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Вывод истории чата
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]
        alignment_class = "from-user" if role == "user" else "from-bot"
        st.markdown(
            f'<div class="chat-row"><div class="chat-message {alignment_class}">{content}</div></div>',
            unsafe_allow_html=True,
        )

    # Поле ввода
    if prompt := st.chat_input("Введите ваш вопрос"):
        if prompt.strip():
            st.session_state.messages.append(
                {"role": "user", "content": prompt}
            )

            # Отобразить сообщение пользователя сразу
            st.markdown(
                f'<div class="chat-row"><div class="chat-message from-user">{prompt}</div></div>',
                unsafe_allow_html=True,
            )

            response_container = st.empty()
            st.session_state.docs_container = st.empty()

            with response_container:
                st.session_state.messages.append(
                    {"role": "assistant", "content": ""}
                )
                documents = None

                for chunk, docs in stream_response(
                    prompt,
                    st.session_state.messages[-10:],
                ):
                    if chunk:
                        st.session_state.messages[-1]["content"] += chunk
                        response_container.markdown(
                            f"<div class='chat-row'><div class='chat-message from-bot'>{st.session_state.messages[-1]['content']}</div></div>",
                            unsafe_allow_html=True,
                        )
                    if docs is not None:
                        documents = docs

                st.session_state.documents = documents


if __name__ == "__main__":
    main_app()
