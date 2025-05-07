import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from openai import OpenAI
from parse_hh import get_html, extract_vacancy_data, extract_resume_data

# Установка лимита попыток при первом запуске
if "launches_left" not in st.session_state:
    st.session_state.launches_left = 5

# Проверка лимита и возможность разблокировки через PIN
if st.session_state.launches_left <= 0:
    st.warning("⛔ Лимит исчерпан. Введите PIN для разблокировки.")

    pin_input = st.text_input("Введите PIN-код для разблокировки:", type="password")
    correct_pin = os.getenv("UNLOCK_PIN")  # PIN хранится в секретах Streamlit

    if pin_input == correct_pin:
        st.session_state.launches_left = 5
        st.success("✅ Доступ успешно разблокирован! У вас снова 5 попыток.")
    else:
        st.stop()

# Инициализация OpenAI-клиента
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.
Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?). Эта оценка должна учитываться при выставлении финальной оценки - нам важно нанимать таких кандидатов, которые могут рассказать про свою работу
Потом представь результат в виде оценки от 1 до 10.
""".strip()

def request_gpt(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
        temperature=0,
    )
    return response.choices[0].message.content

# UI
st.title('CV Scoring App')

# 💡 Показываем, сколько попыток осталось
st.info(f"Осталось попыток: {st.session_state.launches_left}")

job_url = st.text_area('Введите ссылку на вакансию')
resume_url = st.text_area('Введите ссылку на резюме')

if st.button("Проанализировать соответствие"):
    with st.spinner("Парсим данные и отправляем в GPT..."):
        try:
            st.session_state.launches_left -= 1

            job_html = get_html(job_url).text
            resume_html = get_html(resume_url).text

            job_text = extract_vacancy_data(job_html)
            resume_text = extract_resume_data(resume_html)

            prompt = f"# ВАКАНСИЯ\n{job_text}\n\n# РЕЗЮМЕ\n{resume_text}"
            response = request_gpt(SYSTEM_PROMPT, prompt)

            st.subheader("📊 Результат анализа:")
            st.markdown(response)
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")
