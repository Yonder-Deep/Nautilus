import React, { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import {
  Box,
  Button,
  Flex,
  Input,
  InputGroup,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useDisclosure,
  Spacer,
  Center,
  Square,
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
  FormErrorIcon
} from "@chakra-ui/react";

const TestsContext = React.createContext({
  tests: [], fetchtests: () => { }
})

export default function Tests() {

  // const {
  //   handleSubmit,
  //   formState: { errors, isSubmitting }
  // } = useForm();

  // function onSubmit(values) {
  //   return new Promise((resolve) => {
  //     setTimeout(() => {
  //       // alert(JSON.stringify(values, null, 2));
  //       resolve();
  //     }, 3000);
  //   });
  // }

  const [tests, settests] = useState([])

  const fetchtests = async () => {
    const response = await fetch("http://localhost:6543/test") //Place uvicorn server path here to fetch 
    const tests = await response.json()
    settests(tests.data)
  }

  useEffect(() => {
    fetchtests()
  }, [])

  return (
    <TestsContext.Provider value={{ tests, fetchtests }}>

      <Stack spacing={5}>
        {tests.map((test) => (
          <b>{test.item}</b>
        ))}

        <Center>
          <Text fontSize='4xl' >Testing and Calibration</Text>
        </Center>


        <Flex color='white'>
          <Box flex='1' bg='blue'>
            <Text>Graph 1</Text>
          </Box>
          <Box flex='1' bg='red'>
            <Text>Graph 2</Text>
          </Box>
          <Box flex='1' bg='tomato' height="500px">
            <Text>Graph 3</Text>
          </Box>
        </Flex>

        <Flex>
          <Button colorScheme='blue' w='100px'>Test 1</Button>
          <Spacer />
          <Button colorScheme='blue' w='100px'>Test 2</Button>
          <Spacer />
          <Button colorScheme='blue' w='100px'>Test 3</Button>
        </Flex>

        <FormControl>
          <FormLabel>First name:</FormLabel>
          <Input placeholder="Enter your first name..." />
        </FormControl>

        {/* <form onSubmit={handleSubmit(onSubmit)}>
          <FormControl isInvalid={errors.name}>
            <FormLabel htmlFor="name">First name</FormLabel>
            <Input
              id="name"
              placeholder="name"
            />
            <FormErrorMessage>
              {errors.name && errors.name.message}
            </FormErrorMessage>
          </FormControl>
          <Button mt={4} colorScheme="teal" isLoading={isSubmitting} type="submit">
            Submit
          </Button>
        </form> */}

      </Stack>




    </TestsContext.Provider>

  )
}