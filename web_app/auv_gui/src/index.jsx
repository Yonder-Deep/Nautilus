import { ChakraProvider } from "@chakra-ui/react";
import Tests from "./pages/Tests.jsx";  // new

export default function App() {
  return (
    <ChakraProvider>
      <Tests />  {/* new */}
    </ChakraProvider>
  )
}
