import { extendTheme } from "@chakra-ui/react";

const styles = {
  global: {
    body: { color: "white.100" },
    a: { color: "white.100" },
    p: { color: "white.100" },
    h1: { color: "white.100" },
    h2: { color: "white.100" },
    h3: { color: "white.100" },
    h4: { color: "white.100" },
    Heading: { color: "white.100" },
    Text: { color: "white.100" },
    Button: { color: "white.100" },
  },
};

const Theme = extendTheme({ styles });

export default Theme;
