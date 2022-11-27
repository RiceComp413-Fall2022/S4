import {
  SimpleGrid,
  Box,
  Heading,
  CircularProgress,
  CircularProgressLabel,
  Flex,
} from "@chakra-ui/react";

function OverallStat({ label, color, stat }) {
  return (
    <Box w="100%" mt="5%">
      <CircularProgress value={stat} size="100%" color={color}>
        <CircularProgressLabel>
          <Heading textAlign={"center"} w="100%">
            {stat}%
          </Heading>
          <Heading fontSize="xl">{label}</Heading>
        </CircularProgressLabel>
      </CircularProgress>
    </Box>
  );
}

function OverallStats() {
  function Content() {
    return (
      <SimpleGrid
        w="50%"
        columns={[1, null, null, 3]}
        spacing={["0px", null, null, "10px"]}
      >
        <OverallStat label="Overall Health" color="green.400" stat={40} />
        <OverallStat label="Overall Storage" color="blue.400" stat={40} />
        <OverallStat label="Overall RPS" color="purple.400" stat={40} />
      </SimpleGrid>
    );
  }

  return (
    <>
      <Box as="Center" m="7%" display={["inherit", null, null, "none"]}>
        <Content />
      </Box>
      <Box m="5%" display={["none", null, null, "inherit"]}>
        <Flex align="center">
          <Content />
          <Heading fontSize="4xl" ml="5%">
            Overall Statistics
          </Heading>
        </Flex>
      </Box>
    </>
  );
}

export default OverallStats;
