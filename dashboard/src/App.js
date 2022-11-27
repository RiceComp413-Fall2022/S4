import Dashboard from "./Dashboard.jsx";
import * as React from "react";

import { ChakraProvider } from "@chakra-ui/react";

function App() {
  return (
    <ChakraProvider>
      <Dashboard />
    </ChakraProvider>
  );
}

export default App;
