import { createFileRoute, Link } from "@tanstack/react-router";
import styles from "./index.module.css";

export const Route = createFileRoute("/")({
  component: IndexComponent,
});

function IndexComponent() {
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>CopilotKit Demos</h1>
      <p className={styles.subtitle}>
        Explore different examples of CopilotKit integration
      </p>
      <div className={styles.demoList}>
        <Link to="/square-color" className={styles.demoCard}>
          <h2>Square Color Demo</h2>
          <p>
            Interact with an AI assistant to change the color of a square using
            actions and readable state
          </p>
        </Link>
      </div>
    </div>
  );
}
