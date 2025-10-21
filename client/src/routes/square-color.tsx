import {
  useCopilotAction,
  useCopilotReadable,
} from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import styles from "./square-color.module.css";

export const Route = createFileRoute("/square-color")({
  component: SquareColorDemo,
});

function Square({ color = "blue" }) {
  return (
    <div className={styles.square} style={{ backgroundColor: color }} />
  );
}

function SquareColorDemo() {
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
      <CopilotSidebar
        defaultOpen
        clickOutsideToClose={false}
        hitEscapeToClose={false}
        instructions={
          "You are assisting the user as best as you can. Answer in the best way possible given the data you have."
        }
        labels={{
          title: "Your Assistant",
          initial: "Hi! 👋 How can I assist you today?",
        }}
        suggestions={[
          {
            title: "Change square color",
            message: "Choose a new random background color.",
          },
          {
            title: "What is the square color?",
            message: "What is the square color?",
          },
        ]}
      />
      <div className={styles.container}>
        <Link to="/" className={styles.backLink}>
          ← Back to demos
        </Link>
        <Square color={color} />
        <div className={styles.buttonContainer}>
          <button onClick={() => setColor("red")}>Red</button>
          <button onClick={() => setColor("blue")}>Blue</button>
          <button onClick={() => setColor("green")}>Green</button>
          <div className={styles.currentColor}>Current color: {color}</div>
        </div>
      </div>
    </>
  );
}
