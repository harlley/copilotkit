import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="agent">
      <Outlet />
      <TanStackRouterDevtools />
    </CopilotKit>
  );
}
