export type CaseDocument = {
  document: string;
  case_id: string;
  language: string;
  body: string;
  source_file: string;
  delivery: string;
  round: string;
};

const DOCUMENTS_URL =
  "http://localhost:8000/endpoints/documents";

export async function getDocuments(
  signal?: AbortSignal
): Promise<CaseDocument[]> {
  const response = await fetch(DOCUMENTS_URL, { signal });

  if (!response.ok) {
    throw new Error(
      `Could not load documents (${response.status}).`
    );
  }

  const data: unknown = await response.json();

  if (!Array.isArray(data)) {
    throw new Error(
      "Unexpected response: expected an array of documents."
    );
  }

  const validDocuments = data.every(
    (item) =>
      typeof item === "object" &&
      item !== null &&
      typeof item.case_id === "string" &&
      typeof item.delivery === "string" &&
      typeof item.body === "string"
  );

  if (!validDocuments) {
    throw new Error(
      "Some documents are missing their ID, title or body."
    );
  }

  return data as CaseDocument[];
}