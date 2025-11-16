use rayon::prelude::*;
use std::error::Error;
use std::fs::File;
use std::io::{BufWriter, Write};

const N: usize = 8;
const FACT8: usize = 40320;

const LINES: [&[usize]; 8] = [
    &[0, 1, 2],
    &[3, 4],
    &[5, 6, 7],
    &[0, 3, 5],
    &[1, 6],
    &[2, 4, 7],
    &[0, 7],
    &[2, 5],
];

fn heap_permute(k: usize, a: &mut [u8; N], out: &mut Vec<[u8; N]>) {
    if k == 1 {
        out.push(*a);
        return;
    }
    heap_permute(k - 1, a, out);
    for i in 0..(k - 1) {
        if k % 2 == 0 {
            a.swap(i, k - 1);
        } else {
            a.swap(0, k - 1);
        }
        heap_permute(k - 1, a, out);
    }
}

fn generate_permutations() -> Vec<[u8; N]> {
    let mut base: [u8; N] = [1, 2, 3, 4, 5, 6, 7, 8];
    let mut perms = Vec::with_capacity(FACT8);
    heap_permute(N, &mut base, &mut perms);
    perms
}

#[inline]
fn bingo_time_from_calltime(card: &[u8; N], call_time: &[u8; 9]) -> u8 {
    let mut best = u8::MAX;
    for line in LINES.iter() {
        let mut t_line = 0u8;
        for &pos in *line {
            let num = card[pos] as usize;
            let t = call_time[num];
            if t > t_line {
                t_line = t;
            }
        }
        if t_line < best {
            best = t_line;
        }
    }
    best
}

fn main() -> Result<(), Box<dyn Error>> {
    let card_a: [u8; N] = [1, 2, 3, 4, 5, 6, 7, 8];

    let perms = generate_permutations();

    let mut call_times: Vec<[u8; 9]> = Vec::with_capacity(FACT8);
    for perm in perms.iter() {
        let mut ct = [0u8; 9];
        for (i, &num) in perm.iter().enumerate() {
            ct[num as usize] = i as u8;
        }
        call_times.push(ct);
    }

    let a_times: Vec<u8> = call_times
        .iter()
        .map(|ct| bingo_time_from_calltime(&card_a, ct))
        .collect();

    let all_cards = perms; // same set used as cards B

    let results: Vec<(usize, [u8; N], f64)> = all_cards
        .par_iter()
        .enumerate()
        .map(|(idx, card_b)| {
            let mut win_a: u32 = 0;
            let mut draw: u32 = 0;

            for (ct, &t_a) in call_times.iter().zip(a_times.iter()) {
                let t_b = bingo_time_from_calltime(card_b, ct);
                if t_a < t_b {
                    win_a += 1;
                } else if t_a == t_b {
                    draw += 1;
                }
            }

            let p = (win_a as f64 + 0.5 * draw as f64) / (FACT8 as f64);
            (idx, *card_b, p)
        })
        .collect();

    let file = File::create("a_vs_all_other_cards.csv")?;
    let mut writer = BufWriter::new(file);

    writeln!(
        writer,
        "B_index,B0,B1,B2,B3,B4,B5,B6,B7,Prob_A_wins"
    )?;

    for (idx, card_b, p) in results {
        writeln!(
            writer,
            "{},{},{},{},{},{},{},{},{},{}",
            idx,
            card_b[0],
            card_b[1],
            card_b[2],
            card_b[3],
            card_b[4],
            card_b[5],
            card_b[6],
            card_b[7],
            p
        )?;
    }

    writer.flush()?;
    Ok(())
}
