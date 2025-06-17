
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns
import emoji

st.set_page_config(page_title="Instagram DM Analyzer", layout="wide")
st.title("📊 Instagram DM Analyzer")

uploaded_files = st.file_uploader("Upload your message_*.json files", type="json", accept_multiple_files=True)

if uploaded_files:
    all_msgs = []
    msg_counts = defaultdict(int)
    word_counts = defaultdict(int)
    emoji_counts = defaultdict(int)
    reply_times = defaultdict(list)
    first_messages = {}
    chat_durations = {}
    reply_gaps = defaultdict(list)

    for file in uploaded_files:
        data = json.load(file)
        chat_name = data.get("title", "Unknown Chat")
        messages = data.get("messages", [])
        messages = [m for m in messages if m.get("type") == "Generic"]
        messages.reverse()

        last_sender = None
        last_time = None
        first_messages.setdefault(chat_name, f"{messages[0]['sender_name']}: {messages[0].get('content', '')}" if messages else "No messages")

        for msg in messages:
            sender = msg.get("sender_name")
            timestamp = datetime.fromtimestamp(msg["timestamp_ms"] / 1000.0)
            content = msg.get("content", "")

            all_msgs.append({"chat": chat_name, "sender": sender, "content": content, "timestamp": timestamp})
            msg_counts[sender] += 1
            word_counts[sender] += len(content.split())

            for char in content:
                if char in emoji.EMOJI_DATA:
                    emoji_counts[char] += 1

            if last_sender and last_sender != sender and last_time:
                gap = (timestamp - last_time).total_seconds() / 60
                reply_times[sender].append(gap)
                reply_gaps[chat_name].append(gap)

            last_sender = sender
            last_time = timestamp

        if messages:
            chat_durations[chat_name] = (messages[0]["timestamp_ms"], messages[-1]["timestamp_ms"])

    df = pd.DataFrame(all_msgs)
    
    st.write("Total messages loaded:", len(df))
    st.dataframe(df.head())

    st.subheader("🔢 Message Counts")
    counts_df = pd.DataFrame(msg_counts.items(), columns=["Sender", "Messages"]).sort_values(by="Messages", ascending=False)
    st.dataframe(counts_df)

    st.subheader("📊 Message Count Chart")
    fig1, ax1 = plt.subplots()
    sns.barplot(y="Sender", x="Messages", data=counts_df, ax=ax1)
    st.pyplot(fig1)

    st.subheader("📅 Hourly Activity Chart")
    df["hour"] = df["timestamp"].dt.hour
    hourly_counts = df["hour"].value_counts().sort_index()
    fig2, ax2 = plt.subplots()
    sns.barplot(x=hourly_counts.index, y=hourly_counts.values, ax=ax2)
    ax2.set_xlabel("Hour")
    ax2.set_ylabel("Messages")
    st.pyplot(fig2)

    st.subheader("🌡️ Activity Heatmap")
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    heatmap_data = df.groupby(["date", "hour"]).size().unstack(fill_value=0)
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    sns.heatmap(heatmap_data.T, cmap="YlGnBu", ax=ax3)
    ax3.set_xlabel("Date")
    ax3.set_ylabel("Hour")
    st.pyplot(fig3)

    st.subheader("⏱️ Average Reply Time (minutes)")
    avg_reply_df = pd.DataFrame([(k, sum(v)/len(v)) for k, v in reply_times.items()], columns=["Sender", "Avg Reply Time"])
    st.dataframe(avg_reply_df.sort_values(by="Avg Reply Time"))

    st.subheader("🕓 Longest Reply Gaps (minutes) by Chat")
    gap_df = pd.DataFrame([(chat, max(gaps)) for chat, gaps in reply_gaps.items() if gaps], columns=["Chat", "Longest Gap (min)"])
    st.dataframe(gap_df.sort_values("Longest Gap (min)", ascending=False))

    st.subheader("🧠 First Message in Each Chat")
    for chat, msg in first_messages.items():
        st.markdown(f"**{chat}**: {msg}")

    st.subheader("🎭 Emoji Usage")
    emoji_df = pd.DataFrame(Counter(emoji_counts).most_common(10), columns=["Emoji", "Count"])
    st.dataframe(emoji_df)

    st.subheader("⏳ Total Time Span of Each Chat")
    duration_df = pd.DataFrame([
        {"Chat": chat, "Duration (minutes)": (end - start) / 1000 / 60}
        for chat, (start, end) in chat_durations.items()
    ]).sort_values("Duration (minutes)", ascending=False)
    st.dataframe(duration_df)
