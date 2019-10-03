#
# Makefile for vfatqc package
#

BUILD_HOME := $(shell dirname `pwd`)

Project     := vfatqc-python-scripts
ShortProject:= vfatqc
Namespace   := gempython
Package     := vfatqc-python-scripts
ShortPackage:= vfatqc
LongPackage := vfatqc
PackageName := $(Namespace)_$(ShortPackage)
PackageDir  := pkg/$(Namespace)/$(ShortPackage)
ScriptDir   := pkg/$(Namespace)/scripts
INSTALL_PATH=/opt/$(Namespace)

ProjectPath:=$(BUILD_HOME)/$(Project)
ConfigDir:=$(ProjectPath)/config

include $(ConfigDir)/mfCommonDefs.mk
include $(ConfigDir)/mfPythonDefs.mk

# Explicitly define the modules that are being exported (for PEP420 compliance)
PythonModules = ["$(Namespace).$(ShortPackage)", \
                 "$(Namespace).$(ShortPackage).utils", \
]
$(info PythonModules=${PythonModules})

VFATQC_VER_MAJOR:=$(shell $(ConfigDir)/tag2rel.sh | awk '{split($$0,a," "); print a[1];}' | awk '{split($$0,b,":"); print b[2];}')
VFATQC_VER_MINOR:=$(shell $(ConfigDir)/tag2rel.sh | awk '{split($$0,a," "); print a[2];}' | awk '{split($$0,b,":"); print b[2];}')
VFATQC_VER_PATCH:=$(shell $(ConfigDir)/tag2rel.sh | awk '{split($$0,a," "); print a[3];}' | awk '{split($$0,b,":"); print b[2];}')

include $(ConfigDir)/mfSphinx.mk
include $(ConfigDir)/mfPythonRPM.mk

PythonSources=$(wildcard *.py)
PythonSources+=$(wildcard utils/*.py)
PythonSources+=$(wildcard macros/*.py)

default:
	@echo "Running default target"
	$(MakeDir) $(PackageDir)
	@cp -rf utils $(PackageDir)
	@echo "__path__ = __import__('pkgutil').extend_path(__path__, __name__)" > pkg/$(Namespace)/__init__.py
	@cp -rf __init__.py $(PackageDir)

# Override, as this package uses pkg/setup.py as the template file
$(PackageSetupFile): pkg/setup.py
$(PackagePrepFile): $(PythonSources) Makefile | default
	@cp -rf config/scriptlets/installrpm.sh pkg/
	@perl -pi -e "s|__PYTHON_SCRIPT_PATH__|$(INSTALL_PATH)/bin/$(ShortPackage)|g" pkg/installrpm.sh
	$(MakeDir) $(ScriptDir)
	@cp -rf checkSbitMappingAndRate.py $(ScriptDir)
	@cp -rf conf*.py $(ScriptDir)
	@cp -rf dacScanV3.py $(ScriptDir)
	@cp -rf fastLatency.py $(ScriptDir)
	@cp -rf getCalInfoFromDB.py $(ScriptDir)
	@cp -rf iterativeTrim.py $(ScriptDir)
	@cp -rf monitorTemperatures.py $(ScriptDir)
	@cp -rf run_scans.py $(ScriptDir)
	@cp -rf sbitReadOut.py $(ScriptDir)
	@cp -rf sbitThreshScanParallel.py $(ScriptDir)
	@cp -rf testConnectivity.py $(ScriptDir)
	@cp -rf trimChamber.py $(ScriptDir)
	@cp -rf trimChamberV3.py $(ScriptDir)
	@cp -rf ultra*.py $(ScriptDir)
	@cp -rf updateVFAT3ConfFiles.py $(ScriptDir)
	-cp -rf README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt $(PackageDir)
	-cp -rf README.md LICENSE CHANGELOG.md MANIFEST.in requirements.txt pkg

clean:
	@echo "Running clean target"
	-rm -rf $(ScriptDir)
	-rm -rf $(PackageDir)
	-rm -f  pkg/$(Namespace)/__init__.py
	-rm -f  pkg/README.md
	-rm -f  pkg/LICENSE
	-rm -f  pkg/MANIFEST.in
	-rm -f  pkg/CHANGELOG.md
	-rm -f  pkg/requirements.txt
	-rm -f  pkg/installrpm.sh

print-env:
	@echo BUILD_HOME     $(BUILD_HOME)
	@echo GIT_VERSION    $(GIT_VERSION)
	@echo PYTHON_VERSION $(PYTHON_VERSION)
	@echo GEMDEVELOPER   $(GEMDEVELOPER)
