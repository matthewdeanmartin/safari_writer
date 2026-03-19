import nspell from 'nspell';

let cachedChecker: SpellChecker | null = null;

export class SpellChecker {
  private spell: ReturnType<typeof nspell>;

  constructor(aff: string, dic: string) {
    this.spell = nspell(aff, dic);
  }

  check(word: string): boolean {
    return this.spell.correct(word);
  }

  suggest(word: string): string[] {
    return this.spell.suggest(word).slice(0, 5);
  }

  addWord(word: string): void {
    this.spell.add(word);
  }
}

export async function loadSpellChecker(): Promise<SpellChecker> {
  if (cachedChecker) return cachedChecker;

  const [affResp, dicResp] = await Promise.all([
    fetch('/dict/en_US.aff'),
    fetch('/dict/en_US.dic'),
  ]);

  if (!affResp.ok || !dicResp.ok) {
    throw new Error('Failed to load dictionary files');
  }

  const [aff, dic] = await Promise.all([
    affResp.text(),
    dicResp.text(),
  ]);

  cachedChecker = new SpellChecker(aff, dic);
  return cachedChecker;
}
