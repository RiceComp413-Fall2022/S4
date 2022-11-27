import { Box, Heading } from "@chakra-ui/react";
import OverallStats from "./OverallStats";

function Dashboard() {
  return (
    <>
      <Box bgColor="orange.500">
        <Heading pt="5%" px="5%" pb="2%" fontSize="5xl">
          S4 Dashboard
        </Heading>
      </Box>
      <OverallStats />
    </>
  );
}

export default Dashboard;
