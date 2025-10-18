import {
  CopilotKit,
  useCopilotReadable,
  useCopilotAction,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useState } from "react";

function Square({ color = "blue" }) {
  return (
    <div style={{ backgroundColor: color, width: "100px", height: "100px" }} />
  );
}

function YourComponent() {
  const [color, setColor] = useState("blue");

  useCopilotReadable({
    description: "The current color of the square",
    value: color,
  });

  useCopilotAction({
    name: "setSquareColor",
    description: "Set the color of the square",
    parameters: [
      {
        name: "color",
        type: "string",
        description: "The new color for the square",
      },
    ],
    handler: async ({ color }) => {
      setColor(color);
    },
  });

  return (
    <>
      <CopilotChat
        instructions={
          "You are assisting the user as best as you can. Answer in the best way possible given the data you have."
        }
        labels={{
          title: "Your Assistant",
          initial: "Hi! 👋 How can I assist you today?",
        }}
        suggestions={[
          {
            title: "Change background",
            message: "Choose a new random background color.",
          },
          {
            title: "What is the square color?",
            message: "What is the square color?",
          },
        ]}
      />
      <Square color={color} />
      <div style={{ marginTop: "20px", display: "flex", gap: "10px", alignItems: "center" }}>
        <button onClick={() => setColor("red")}>Red</button>
        <button onClick={() => setColor("blue")}>Blue</button>
        <button onClick={() => setColor("green")}>Green</button>
        <div style={{ marginLeft: "20px", fontWeight: "bold" }}>
          Current color: {color}
        </div>
      </div>
    </>
  );
}

function App() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="agent">
      <YourComponent />
    </CopilotKit>
  );
}

export default App;
