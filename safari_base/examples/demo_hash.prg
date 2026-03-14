* demo_hash.prg
* Illustrates hashmap extensions in the dBASE language.

? "--- Safari Base Hashmap Extension Demo ---"
? ""

DIM config{}

? "Setting keys in hashmap config..."
config("user") = "matt"
config("theme") = "dark"
config("port") = 8080

? "Accessing keys:"
? "User: " + config("user")
? "Theme: " + config("theme")
? "Port: " + STR(config("port"))

? ""
? "Iterating over keys using FOR EACH:"
FOR EACH k IN config
    IF k = "port"
        ? "Key: " + k + " = " + STR(config(k))
    ELSE
        ? "Key: " + k + " = " + config(k)
    ENDIF
ENDFOR

? ""
? "Hashmaps allow easy structured data without a table."
? "Demo completed."
