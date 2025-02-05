#import <Foundation/Foundation.h>
#import <IOKit/IOTypes.h>
#import <IOKit/IOKitKeys.h>
#import <IOKit/usb/IOUSBLib.h>
#import <sys/param.h>
#import <paths.h>

int main() {
    NSLog(@"Hello World");

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
    
    NSLog(@"Matching Dict:");
    NSLog(@"%@", matchingUSBDict);

    // Find the first service in the I/O Registry that matches our dictionary
    io_service_t matchedService;
    matchedService = IOServiceGetMatchingService(kIOMainPortDefault, matchingUSBDict);

    NSLog(@"Service: %u", matchedService);
    
    // Service path, not really that useful for our purposes
    io_string_t servicePath;
    IORegistryEntryGetPath(matchedService, kIOServicePlane, servicePath);
    NSLog(@"Service Path: %s", servicePath);

    // This is the name appended to the filepath: /dev/tty.usbserial-[BSDName]
    CFStringRef deviceBSDName_cf = (CFStringRef) IORegistryEntrySearchCFProperty(matchedService,
            kIOServicePlane,
            CFSTR (kUSBSerialNumberString),
            kCFAllocatorDefault,
            kIORegistryIterateRecursively );
    NSLog(@"BSD Name: %@", deviceBSDName_cf);

    char deviceFilePath[MAXPATHLEN]; // MAXPATHLEN is defined in sys/param.h
    size_t devPathLength;
    Boolean gotString = false;

    /*CFTypeRef deviceNameAsCFString;
    deviceNameAsCFString = IORegistryEntryCreateCFProperty (
            matchedService,
            CFSTR(kIOBSDNameKey),
            kCFAllocatorDefault, 0);
    NSLog(@"hi");
    NSLog(@"%@", deviceNameAsCFString);*/
    if (deviceBSDName_cf) {
        NSLog(@"Hello World 4");
        char deviceFilePath[MAXPATHLEN];
        devPathLength = strlen(_PATH_DEV); //_PATH_DEV defined in paths.h
        strcpy(deviceFilePath, _PATH_DEV);
        strcat(deviceFilePath, "r");
        gotString = CFStringGetCString(deviceBSDName_cf,
                deviceFilePath + strlen(deviceFilePath),
                MAXPATHLEN - strlen(deviceFilePath),
                kCFStringEncodingASCII);
        
        if (gotString) {
            NSLog(@"Device file path: %s", deviceFilePath);
        }
    }

	return 0;
}
