import {
  Box,
  SimpleGrid,
  Heading,
  Flex,
  Icon,
  Text,
  Spacer,
} from "@chakra-ui/react";
import { AiFillCheckCircle, AiFillMinusCircle } from "react-icons/ai";
 
function NodeStats({everything}) {
  return (
    <Box bgColor="#ffeebd">
      <SimpleGrid columns={[1, 2, 3, 4]} px="5%" py="2%">
        {everything.map((item, idx) => {
          return <NodeStat key={idx} num={idx} ip={item[0]} health={item[2]} listO={item[1]} diskUsage={item[3]} filesForNode={item[4]}/>;
        })}
      </SimpleGrid>
    </Box>
  );
}
function NodeStat({ num, ip, health, listO, diskUsage, filesForNode}) {
  return (
    <Box w="100%" pr="8%" py="3%">
      <Box rounded="lg" bgColor="#eebd8b" style={{ aspectRatio: 1 }} p="5%">
        <Flex align="center">
          <Heading fontSize="xl" ml="5%">
            Node {num}
          </Heading>
          <Spacer />
          <Icon
            as={health ? AiFillCheckCircle : AiFillMinusCircle}
            color={health ? "#20a47b" : "red.400"}
            boxSize="25px"
            mr="5%"
          />
        </Flex>
        <Heading p="5%" fontSize="sm">
          IP: {ip} Storage Used: {diskUsage}%
        </Heading>
        <Box
          overflowY={"scroll"}
          m="3%"
          p="5%"
          rounded="lg"
          bgColor="#9c5a4a"
          maxH="75%"
          position="relative"
          minH="75%"
        >
          {!health && (
            <Box
              position="absolute"
              top="0"
              right="0"
              w="100%"
              h="100%"
              bgColor="black"
              opacity="0.5"
            />
          )}
          <Heading fontSize="lg" mb="2px">
            Files
          </Heading>
          {filesForNode.map((item, idx) => (
            <Text key={idx}>{item}</Text>
          ))}
        </Box>
      </Box>
    </Box>
  );
}

export default NodeStats;