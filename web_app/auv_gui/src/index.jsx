import { ChakraProvider } from "@chakra-ui/react";
import Tests from "./components/Test";  // new

export default function App() {
  return (
    <ChakraProvider>
      <Tests />  {/* new */}
    </ChakraProvider>
  )
}