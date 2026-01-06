CMAKE_MINIMUM_REQUIRED(VERSION 3.5)

project(obviews)


# look for OTAWA
if(NOT OTAWA_CONFIG)
	find_program(OTAWA_CONFIG otawa-config DOC "path to otawa-config")
	if(NOT OTAWA_CONFIG)
		message(FATAL_ERROR "ERROR: otawa-config is required !")
	endif()
endif()
message(STATUS "otawa-config at ${OTAWA_CONFIG}")

execute_process(COMMAND "${OTAWA_CONFIG}" --prefix  OUTPUT_VARIABLE OTAWA_PREFIX  OUTPUT_STRIP_TRAILING_WHITESPACE)
execute_process(COMMAND "${OTAWA_CONFIG}" --bindir  OUTPUT_VARIABLE OTAWA_BINDIR  OUTPUT_STRIP_TRAILING_WHITESPACE)
execute_process(COMMAND "${OTAWA_CONFIG}" --datadir OUTPUT_VARIABLE OTAWA_DATADIR OUTPUT_STRIP_TRAILING_WHITESPACE)

# installation
install(FILES     "bin/obviews.py" DESTINATION "${OTAWA_BINDIR}"
	PERMISSIONS OWNER_EXECUTE OWNER_READ)
install(DIRECTORY "data/obviews"   DESTINATION	"${OTAWA_DATADIR}")

