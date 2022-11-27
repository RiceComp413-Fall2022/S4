import { Box, SimpleGrid } from "@chakra-ui/react";
function NodeStats() {
  return (
    <Box bgColor="#ffeebd">
      <SimpleGrid columns={[1, 2, 3, 4]} px="5%" py="2%">
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
        <NodeStat />
      </SimpleGrid>
    </Box>
  );
}
function NodeStat() {
  return (
    <Box w="100%" px="5%" py="2%">
      <Box rounded="lg" bgColor="#eebd8b" style={{ aspectRatio: 1 }}>
        asdfasdf
      </Box>
    </Box>
  );
}

export default NodeStats;
