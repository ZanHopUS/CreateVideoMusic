export function reviewState(rows, sourceTime) {
  const index = rows.findIndex(row => sourceTime >= row.cue.start_s && sourceTime < row.cue.end_s);
  if (index < 0) return {index: -1, row: null, activeWord: -1};
  const row = rows[index];
  const activeWord = row.mode === 'word_draft'
    ? row.words.findIndex(word => sourceTime >= word.start && sourceTime < word.end)
    : -1;
  return {index, row, activeWord};
}
