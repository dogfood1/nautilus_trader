// -------------------------------------------------------------------------------------------------
//  Copyright (C) 2015-2023 Nautech Systems Pty Ltd. All rights reserved.
//  https://nautechsystems.io
//
//  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
//  You may not use this file except in compliance with the License.
//  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
// -------------------------------------------------------------------------------------------------

use std::{
    collections::hash_map::DefaultHasher,
    ffi::c_char,
    hash::{Hash, Hasher},
};

use nautilus_core::string::str_to_cstr;

use super::trade::TradeTick;
use crate::{
    enums::AggressorSide,
    identifiers::{instrument_id::InstrumentId, trade_id::TradeId},
    types::{price::Price, quantity::Quantity},
};

#[no_mangle]
pub extern "C" fn trade_tick_new(
    instrument_id: InstrumentId,
    price_raw: i64,
    price_prec: u8,
    size_raw: u64,
    size_prec: u8,
    aggressor_side: AggressorSide,
    trade_id: TradeId,
    ts_event: u64,
    ts_init: u64,
) -> TradeTick {
    TradeTick::new(
        instrument_id,
        Price::from_raw(price_raw, price_prec),
        Quantity::from_raw(size_raw, size_prec),
        aggressor_side,
        trade_id,
        ts_event,
        ts_init,
    )
}

#[no_mangle]
pub extern "C" fn trade_tick_drop(tick: TradeTick) {
    drop(tick); // Memory freed here
}

#[no_mangle]
pub extern "C" fn trade_tick_clone(tick: &TradeTick) -> TradeTick {
    tick.clone()
}

#[no_mangle]
pub extern "C" fn trade_tick_eq(lhs: &TradeTick, rhs: &TradeTick) -> u8 {
    u8::from(lhs == rhs)
}

#[no_mangle]
pub extern "C" fn trade_tick_hash(delta: &TradeTick) -> u64 {
    let mut hasher = DefaultHasher::new();
    delta.hash(&mut hasher);
    hasher.finish()
}

/// Returns a [`TradeTick`] as a C string pointer.
#[no_mangle]
pub extern "C" fn trade_tick_to_cstr(tick: &TradeTick) -> *const c_char {
    str_to_cstr(&tick.to_string())
}