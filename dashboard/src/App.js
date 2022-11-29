import Dashboard from "./pages/Dashboard.jsx";
import * as React from "react";
import Theme from "./theme.js";
import { ChakraProvider } from "@chakra-ui/react";

function App() {
  return (
    <ChakraProvider theme={Theme}>
      <Dashboard />
    </ChakraProvider>
  );
}

export default App;
