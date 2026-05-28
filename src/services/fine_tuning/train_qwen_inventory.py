import json
from pathlib import Path

import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_NAME = "unsloth/Qwen2.5-3B-Instruct"
MAX_SEQ_LENGTH = 1024
OUTPUT_DIR = PROJECT_ROOT / "qwen_inventory_model"
DATASET_PATH = PROJECT_ROOT / "src" / "datasets" / "inventory_dataset.jsonl"

TRAIN_SYSTEM_PROMPT = """Voce e um agente de inventario.

Use apenas ferramentas disponiveis como fonte da verdade.
Nunca invente dados de estoque, preco, pedido, fornecedor ou movimentacao.
Quando faltar dado, indique a ferramenta correta ou peca uma confirmacao curta.
Priorize ruptura, estoque baixo, estoque negativo, produtos inativos, movimentacao de estoque e recomendacoes operacionais.
Sempre responda em portugues brasileiro.
"""


def build_assistant_content(tool_choice: list[str], response: str) -> str:
    return json.dumps(
        {
            "tool_choice": tool_choice,
            "response": response,
        },
        ensure_ascii=False,
    )


def formatting_prompt_func(examples, tokenizer):
    texts = []

    for instruction, tool_choice, response in zip(
        examples["instruction"],
        examples["tool_choice"],
        examples["response"],
    ):
        messages = [
            {"role": "system", "content": TRAIN_SYSTEM_PROMPT},
            {"role": "user", "content": instruction},
            {
                "role": "assistant",
                "content": build_assistant_content(tool_choice, response),
            },
        ]

        texts.append(
            tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        )

    return {"text": texts}


def main():
    print("Loading model...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )

    print("Applying LoRA...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )

    print("Loading dataset...")

    dataset = load_dataset(
        "json",
        data_files=str(DATASET_PATH),
        split="train",
    )

    dataset = dataset.map(
        lambda examples: formatting_prompt_func(examples, tokenizer),
        batched=True,
        remove_columns=dataset.column_names,
    )

    print("Starting trainer...")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            warmup_steps=10,
            num_train_epochs=3,
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=str(OUTPUT_DIR),
            report_to="none",
            save_strategy="epoch",
        ),
    )

    print("Training...")
    trainer.train()

    print("Saving model...")
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    print("Done!")


if __name__ == "__main__":
    main()
