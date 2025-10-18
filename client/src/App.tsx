import "@copilotkit/react-ui/styles.css";
import {
  CopilotKit,
  useFrontendTool,
  useCopilotReadable,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { useState } from "react";

function Square({ color = "blue" }) {
  return (
    <div style={{ backgroundColor: color, width: "100px", height: "100px" }} />
  );
}

function YourComponent() {
  const [color, setColor] = useState("blue");

  useCopilotReadable({
    description: "Current color of the square (currently: " + color + ")",
    value: { currentSquareColor: color },
  });

  useFrontendTool({
    name: "setSquareColor",
    description: "Set the color of the square",
    parameters: [
      {
        name: "color",
        type: "string",
        description: "The new color for the square",
        required: true,
      },
    ],
    handler: ({ color }) => {
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
            message: "Change the background to something new.",
          },
          {
            title: "Qual a cor do quadrado?",
            message: "Qual a cor do quadrado?",
          },
        ]}
      />
      <Square color={color} />
      <button onClick={() => setColor("red")}>Red</button>
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
