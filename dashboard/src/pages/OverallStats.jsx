import {
  SimpleGrid,
  Box,
  Heading,
  CircularProgress,
  CircularProgressLabel,
  Flex,
  HStack,
} from "@chakra-ui/react";

/**
 * @param label label of the stat
 * @param color color of the stat
 * @param stat statistic to display
 * @returns Circular component showing stat
 */
function OverallStat({ label, color, stat }) {
  /**
   * @returns Desktop version of stat
   */
  function DesktopStat() {
    return (
      <Box w="100%" mt="5%" display={["none", null, "inherit", "inherit"]}>
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

  /**
   * @returns mobile version of stat
   */
  function MobileStat() {
    return (
      <HStack w="100%" mt="5%" display={["flex", null, "none", "none"]}>
        <Box h="100%" mr="40px">
          <CircularProgress value={stat} size="20vw" color={color}>
            <CircularProgressLabel>
              <Heading fontSize="2xl" textAlign={"center"}>
                {stat}%
              </Heading>
            </CircularProgressLabel>
          </CircularProgress>
        </Box>
        <Flex align="center" h="100%">
          <Heading>{label}</Heading>
        </Flex>
      </HStack>
    );
  }

  return (
    <>
      <DesktopStat />
      <MobileStat />
    </>
  );
}

/**
 * @param everything all stats used for overall stats
 * @returns Component showing overall stats of the system
 */
function OverallStats({ everything }) {
  var [
    size,
    totalHealthy,
    percentHealthy,
    totalStorage,
    usedStorage,
    percentUsedStorage,
  ] = [0, 0, 0, 0, 0, 0];

  everything.map((x, i) => {
    size++;
    if (x[2] === true) {
      totalHealthy++;
    }
    usedStorage += x[3];
    totalStorage += 100;
  });

  percentHealthy = Math.round((totalHealthy / size) * 100);
  percentUsedStorage = Math.round((usedStorage / totalStorage) * 100);

  /**
   * @returns Grid of circular components for each overall stat
   */
  function Content() {
    return (
      <SimpleGrid
        columns={[1, null, 3, 3]}
        spacing={["0px", null, null, "10px"]}
        w="50%"
      >
        <OverallStat label="Health" color="green.400" stat={percentHealthy} />
        <OverallStat
          label="Storage"
          color="blue.400"
          stat={percentUsedStorage}
        />
      </SimpleGrid>
    );
  }

  return (
    <Box bgColor="#186a62">
      <Box p="5%" w="100%" display={["inherit", null, "none", "none"]}>
        <Content />
      </Box>
      <Box p="5%" display={["none", null, "inherit", "inherit"]}>
        <Flex align="center">
          <Content />
          <Heading fontSize="5xl" ml="1%">
            Overall Statistics
          </Heading>
        </Flex>
      </Box>
    </Box>
  );
}

export default OverallStats;