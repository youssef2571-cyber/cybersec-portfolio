#!/bin/bash
while true
do
  clear
  echo -n " ===============================================
 ==                RSA ALGORITHM              ==  
 ===============================================
 	1. Keys Generation
	2. RSA Keys
	3. Encryption
	4. Decryption
	5. Signature
	6. Check Signature
	7. Quit
 ===============================================

 	Select an Option :  "
	read rep
	case $rep in
	  1|g|G) bash generation.sh;
 	      echo
	      echo -n "	    Press ENTER to continue !";
	      read ;;
	  2|k|K) bash display.sh;
 	      echo
 	      echo -n "	    Press ENTER to continue !";
	      read ;;
          3|e|E) bash encrypt.sh;
 	      echo
 	      echo -n "	    Press ENTER to continue !";
	      read ;;
          4|d|D) bash decrypt.sh;
 	      echo
 	      echo -n "	    Press ENTER to continue !";
	      read ;;
	  5|s|S) bash sign.sh;
 	      echo
 	      echo -n "	    Press ENTER to continue !";
	      read ;;
      	  6|c|C) bash checksign.sh;
 	      echo
 	      echo -n "	    Press ENTER to continue !";
	      read ;;
	  7|q|Q) exit;;
 	   *) echo "Error - Bad Option !!!";
 	      echo
 	      echo -n "	    Press ENTER to continue !";
	      read ;;
	esac
done

