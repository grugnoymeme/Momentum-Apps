#pragma once
#include <furi.h>
#include <furi_hal_version.h>

// Check if we're building for Momentum firmware
#if defined(FW_ORIGIN_NoName)
#include <noname/noname.h>
#define HAS_NONAME_SUPPORT 1
#endif
