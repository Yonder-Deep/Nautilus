#import <Foundation/Foundation.h>
#import <IOKit/IOTypes.h>
#import <IOKit/IOKitKeys.h>
#import <IOKit/usb/IOUSBLib.h>
#import <IOKit/IOBSD.h>
#import <sys/param.h>
#import <paths.h>
#import <stdlib.h>

char* find_radio() {
    //NSLog(@"Finding path to radio device...");

    // Create subdictionary key-pair to match radio USB UART
    CFMutableDictionaryRef subDict;
    subDict = CFDictionaryCreateMutable(kCFAllocatorDefault, 0,
            &kCFTypeDictionaryKeyCallBacks,
            &kCFTypeDictionaryValueCallBacks);
    CFDictionarySetValue(subDict, CFSTR("kUSBProductString"),
            CFSTR("FT231X USB UART"));

    // Add to matching dictionary w/ catch-all "kIOPropertyMatchKey"
    CFMutableDictionaryRef matchingUSBDict;
    matchingUSBDict = CFDictionaryCreateMutable(kCFAllocatorDefault, 0,
            &kCFTypeDictionaryKeyCallBacks,
            &kCFTypeDictionaryValueCallBacks);
    CFDictionarySetValue(matchingUSBDict, CFSTR(kIOPropertyMatchKey),
            subDict);
    
    //NSLog(@"Matching Dict:");
    //NSLog(@"%@", matchingUSBDict);

    // Find the first service in the I/O Registry that matches our dictionary
    io_service_t matchedService;
    matchedService = IOServiceGetMatchingService(kIOMainPortDefault, matchingUSBDict);

    //NSLog(@"Service: %u", matchedService);
    
    // Service path, not really that useful for our purposes
    io_string_t servicePath;
    IORegistryEntryGetPath(matchedService, kIOServicePlane, servicePath);
    //NSLog(@"Service Path: %s", servicePath);
    //NSLog(@"USB Path: %d", IORegistryEntryGetPath(matchedService, kIOPowerPlane, servicePath));

    // This is the [BSDName] appended to the filepath: /dev/tty.usbserial-[BSDName]
    CFStringRef deviceBSDName_cf = (CFStringRef) IORegistryEntrySearchCFProperty(
            matchedService,
            kIOServicePlane,
            CFSTR (kUSBSerialNumberString),
            kCFAllocatorDefault,
            kIORegistryIterateRecursively );
    //NSLog(@"BSD Name: %@", deviceBSDName_cf);

    char deviceFilePath[MAXPATHLEN]; // MAXPATHLEN is defined in sys/param.h
    size_t devPathLength;
    Boolean gotString = false;

    /* This commented part is from the Apple docs but always comes up null    
    CFTypeRef deviceNameAsCFString;
    deviceNameAsCFString = (CFStringRef) IORegistryEntrySearchCFProperty (
            matchedService,
            kIOServicePlane,
            CFSTR(kIOBSDNameKey),
            kCFAllocatorDefault,
            kIORegistryIterateRecursively);
    NSLog(@"hi");
    NSLog(@"%@", deviceNameAsCFString);*/

    if (deviceBSDName_cf) {
        //NSLog(@"BSDName found, finding path...");
        char deviceFilePath[MAXPATHLEN];
        devPathLength = strlen(_PATH_DEV); //_PATH_DEV defined in paths.h
        strcpy(deviceFilePath, _PATH_DEV);
        strcat(deviceFilePath, "tty.usbserial-");
        gotString = CFStringGetCString(deviceBSDName_cf,
                deviceFilePath + strlen(deviceFilePath),
                MAXPATHLEN - strlen(deviceFilePath),
                kCFStringEncodingASCII);
        
        if (gotString) {
            //NSLog(@"Device file path: %s", deviceFilePath);
            char* finalResult = malloc(strlen(deviceFilePath));
            strcpy(finalResult, deviceFilePath);
            //NSLog(@"Pointer address: %p", finalResult);
            return finalResult;
        } /*else {
            NSLog(@"Radio device not found.");
        }*/
    }/* else {
        NSLog(@"Radio device not found.");
    }*/
    char* notFound = malloc(21);
    strcpy(notFound, "Radio device not found");
    //NSLog(@"Pointer address: %p", notFound);
    return notFound;
}

void free_ptr(char* ptr) {
    NSLog(@"Freeing %p", ptr);
    free(ptr);
}

int main() {
    char* result = find_radio();
    printf("%s", result);
    free(result);

    /*
    char* result = find_radio();
    NSLog(@"Result: %s", result);
    setenv("USB_RADIO_PATH", result, 1); // Integer 1 to overwrite if already set
    NSString *radioPath = [NSString stringWithUTF8String:result];
    free(result);

    
    if (radioPath && ![radioPath isEqual: @"Radio device not found"]) {
        NSLog(@"Calling pppd for device at %@", radioPath);
        NSTask *task = [[NSTask alloc] init];
        task.launchPath = @"/usr/sbin/pppd";
        task.arguments = @[
                radioPath,
                @"57600",
                @"nodetach",
                @"lock",
                @"local",
                @"192.168.100.10:192.168.100.11"
                ];

        NSPipe *outputPipe = [NSPipe pipe];
        [task setStandardInput:[NSPipe pipe]];
        [task setStandardOutput:outputPipe];

        [task launch];
        [task waitUntilExit];
        [task release];

        NSData *outputData = [[outputPipe fileHandleForReading] readDataToEndOfFile];
        NSString *outputString = [[[NSString alloc] initWithData:outputData encoding:NSUTF8StringEncoding] autorelease];
        NSLog(@"Output: ");
        NSLog(@"%@", outputString);
    } else {
        NSLog(@"Not calling pppd.");
    }
    NSLog(@"Exiting.");
    */
    return 0;
}
