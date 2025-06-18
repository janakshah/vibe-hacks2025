import { FaMicrophone, FaStop, FaPaperPlane } from "react-icons/fa";
import useSpeechToText from "react-hook-speech-to-text";
import "./App.css";
import logo from "./assets/logo.png";
import axios from "axios";

function App() {
  const {
    error,
    interimResult,
    isRecording,
    results,
    startSpeechToText,
    stopSpeechToText,
  } = useSpeechToText({
    continuous: true,
    useLegacyResults: false,
  });

  if (error) {
    return <p className="error">Web Speech API is not available 🤷‍</p>;
  }

  // Combine all final results into one string
  const finalTranscript = results.map((r) => r.transcript).join(" ");

  // inside your App component, below `finalTranscript` definition:

    const sendTranscript = async () => {
    const payload = {
      transcript: "We're Tony's Pizza in Manhattan 10001 doing buy one get one free today only!",
      send_whatsapp: true,
    };

    try {
      const { data } = await axios.post(
        "http://192.168.1.42:8000/process_transcript",
        payload
      );
      console.log("Server response:", data);
      alert("Transcript processed and message sent!");
    } catch (error) {
      console.error("Error sending transcript:", error);
      alert("Error sending transcript. Check console for details.");
    }
  };

  return (
    <div className="container">
      <header className="header">
        <img src={logo} alt="Logo" className="logo-img" />
        <span className="app-title">Buzz Drop</span>
      </header>

      <button
        className={isRecording ? "stop-btn" : "mic-btn"}
        onClick={isRecording ? stopSpeechToText : startSpeechToText}
      >
        {isRecording ? <FaStop size={48} /> : <FaMicrophone size={48} />}
      </button>

      <p className="status">
        {isRecording
          ? interimResult || "Listening…"
          : finalTranscript
          ? finalTranscript
          : "Click to Record"}
      </p>

      {/* Show send button only when recording is stopped and there is text */}
      {true && (
        <div className="send-wrapper">
          <button className="send-btn" onClick={sendTranscript}>
            Send
            <FaPaperPlane size={20} />
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
