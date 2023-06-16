/* Generated with cbindgen:0.24.5 */

/* Warning, this file is autogenerated by cbindgen. Don't modify this manually. */

#include <stdint.h>
#include <Python.h>

/**
 * Represents a synthetic instrument with prices derived from component instruments using a
 * formula.
 */
typedef struct SyntheticInstrument SyntheticInstrument;

/**
 * Provides a C compatible Foreign Function Interface (FFI) for an underlying
 * [`SyntheticInstrument`].
 *
 * This struct wraps `SyntheticInstrument` in a way that makes it compatible with C function
 * calls, enabling interaction with `SyntheticInstrument` in a C environment.
 *
 * It implements the `Deref` trait, allowing instances of `SyntheticInstrument_API` to be
 * dereferenced to `SyntheticInstrument`, providing access to `SyntheticInstruments`'s methods without
 * having to manually access the underlying instance.
 */
typedef struct SyntheticInstrument_API {
    struct SyntheticInstrument *_0;
} SyntheticInstrument_API;

/**
 * # Safety
 *
 * - Assumes `components_ptr` is a valid C string pointer of a JSON format list of strings.
 * - Assumes `formula_ptr` is a valid C string pointer.
 */
struct SyntheticInstrument_API synthetic_instrument_new(Symbol_t symbol,
                                                        uint8_t precision,
                                                        const char *components_ptr,
                                                        const char *formula_ptr);

void synthetic_instrument_drop(struct SyntheticInstrument_API synth);

InstrumentId_t synthetic_instrument_id(const struct SyntheticInstrument_API *synth);

uint8_t synthetic_instrument_precision(const struct SyntheticInstrument_API *synth);

const char *synthetic_instrument_formula_to_cstr(const struct SyntheticInstrument_API *synth);

const char *synthetic_instrument_components_to_cstr(const struct SyntheticInstrument_API *synth);

/**
 * # Safety
 *
 * - Assumes `formula_ptr` is a valid C string pointer.
 */
uint8_t synthetic_instrument_is_valid_formula(const struct SyntheticInstrument_API *synth,
                                              const char *formula_ptr);

/**
 * # Safety
 *
 * - Assumes `formula_ptr` is a valid C string pointer.
 */
void synthetic_instrument_change_formula(struct SyntheticInstrument_API *synth,
                                         const char *formula_ptr);

Price_t synthetic_instrument_calculate(struct SyntheticInstrument_API *synth,
                                       const CVec *inputs_ptr);
