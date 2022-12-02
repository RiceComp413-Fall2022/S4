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

 // need to fix disk={du(item)

function NodeStats({nodeList, ec, lo, hc, du}) {
  return (
    <Box bgColor="#ffeebd">
      <SimpleGrid columns={[1, 2, 3, 4]} px="5%" py="2%">
        {nodeList.map((item, idx) => {
          return <NodeStat key={idx} num={idx} ip={item} health={hc(item)} />;
        })}
      </SimpleGrid>
    </Box>
  );
}
function NodeStat({ num, ip, health}) { // add 'disk' here 
  return (
    <Box w="100%" pr="8%" py="3%">
      <Box rounded="lg" bgColor="#eebd8b" style={{ aspectRatio: 1 }} p="5%">
        <Flex align="center">
          <Heading fontSize="l" ml="5%">
            Node {num}, IP: {ip}
          </Heading>
          <Spacer />
          <Icon
            as={health ? AiFillCheckCircle : AiFillMinusCircle}
            color={health ? "#20a47b" : "red.400"}
            boxSize="25px"
            mr="5%"
          />
        </Flex>
        <Heading p="5%" fontSize="l">
          Storage Used: disk
        </Heading>
        <Box
          overflowY={"auto"}
          m="3%"
          p="5%"
          rounded="lg"
          bgColor="#9c5a4a"
          maxH="75%"
          position="relative"
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
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
          <Text>asdf</Text>
        </Box>
      </Box>
    </Box>
  );
}

export default NodeStats;