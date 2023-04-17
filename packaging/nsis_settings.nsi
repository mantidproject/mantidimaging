!include "MUI2.nsh"

RequestExecutionLevel admin
Unicode true
!define PRODUCT "Mantid Imaging"

Name "${PRODUCT}"
OutFile "dist\${PRODUCT} Setup.exe"

InstallDir "$PROGRAMFILES64"

!define MUI_ICON "../images/mantid_imaging_unstable_64px.ico"

!insertmacro MUI_PAGE_LICENSE "../LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

Section
	SetShellVarContext all
	SetOutPath $INSTDIR
	File /r dist\MantidImaging
	CreateDirectory "$SMPROGRAMS\${PRODUCT}"
	CreateShortCut "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk" "$INSTDIR\MantidImaging\MantidImaging.exe" \
	   "" "$INSTDIR\MantidImaging\MantidImaging.exe" 0

	WriteUninstaller "$INSTDIR\MantidImaging\uninstall.exe"
SectionEnd

Section "Uninstall"
	SetShellVarContext all
	Delete "$SMPROGRAMS\${PRODUCT}\${PRODUCT}.lnk"
	Delete $INSTDIR\uninstall.exe
	RMDir /r "$INSTDIR"
SectionEnd